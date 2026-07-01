from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.store import Store
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.user import UserCreate, UserIdentityRead, UserLogin, UserRead, UserRegister, UserUpdate
from app.utils.hash_utils import hash_password, verify_password
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/users", tags=["users"])


def _serialize_user(user: User) -> dict:
    return UserRead.model_validate(user).model_dump()


def _location_name(user: User, db: Session) -> str | None:
    if user.location_type == "warehouse" and user.warehouse_id:
        warehouse = db.get(Warehouse, user.warehouse_id)
        return warehouse.name if warehouse else None
    if user.location_type == "store" and user.store_id:
        store = db.get(Store, user.store_id)
        return store.name if store else None
    return None


@router.get("")
def list_users(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(User)
    if keyword:
        query = query.where(
            or_(
                User.username.contains(keyword),
                User.employee_no.contains(keyword),
                User.real_name.contains(keyword),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [_serialize_user(item) for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.post("")
def create_user(payload: UserCreate, db: Session = Depends(get_db_dep)):
    user = User(
        **payload.model_dump(exclude={"password", "verification_code"}),
        password_hash=hash_password(payload.password),
        verification_code_hash=hash_password(payload.verification_code),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(_serialize_user(user))


@router.get("/identity/{employee_no}")
def get_user_identity(employee_no: str, db: Session = Depends(get_db_dep)):
    normalized_employee_no = employee_no.strip().upper()
    user = db.scalar(select(User).where(User.employee_no == normalized_employee_no))
    if not user:
        raise BusinessException("工号不存在，请联系系统管理员核对员工档案", 404)

    identity = UserIdentityRead(
        employee_no=user.employee_no,
        role=user.role,
        location_type=user.location_type,
        warehouse_id=user.warehouse_id,
        store_id=user.store_id,
        location_name=_location_name(user, db),
        is_verified=user.is_verified,
    )
    return success_response(identity.model_dump())


@router.post("/register")
def register_user(payload: UserRegister, db: Session = Depends(get_db_dep)):
    user = db.scalar(select(User).where(User.employee_no == payload.employee_no))
    if not user:
        raise BusinessException("工号不存在，请联系系统管理员核对员工档案", 404)
    if user.is_verified:
        raise BusinessException("该工号已完成账号激活，请直接登录", 409)
    if (user.real_name or "") != payload.real_name:
        raise BusinessException("姓名与工号档案不匹配", 403)
    if (user.phone or "") != payload.phone:
        raise BusinessException("手机号与工号档案不匹配", 403)
    if not verify_password(payload.verification_code, user.verification_code_hash):
        raise BusinessException("验证码错误，请联系管理员重新获取", 403)

    user.password_hash = hash_password(payload.password)
    user.is_verified = True
    user.is_active = True

    db.commit()
    db.refresh(user)
    return success_response(_serialize_user(user), message="注册成功")


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db_dep)):
    normalized_login_name = payload.username.strip()
    normalized_employee_no = normalized_login_name.upper()
    user = db.scalar(
        select(User).where(
            or_(
                User.username == normalized_login_name,
                User.employee_no == normalized_employee_no,
            )
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise BusinessException("工号或密码错误", 401)
    if not user.is_active:
        raise BusinessException("该账号已停用", 403)
    if not user.is_verified:
        raise BusinessException("该工号尚未完成账号激活，请先注册验证", 403)
    if payload.role and payload.role != user.role:
        raise BusinessException("所选角色与账号身份不匹配", 403)
    return success_response(
        _serialize_user(user),
        message="登录成功",
    )


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    return success_response(_serialize_user(user))


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    for key, value in payload.model_dump(exclude_unset=True, exclude={"password", "verification_code"}).items():
        setattr(user, key, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.verification_code:
        user.verification_code_hash = hash_password(payload.verification_code)
    db.commit()
    db.refresh(user)
    return success_response(_serialize_user(user))


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    user.is_active = False
    db.commit()
    return success_response(message="deleted")
