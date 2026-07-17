import secrets
import threading
import time

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep, require_admin
from app.core.auth import create_access_token
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.store import Store
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.user import UserCreate, UserIdentityRead, UserLogin, UserRead, UserRegister, UserUpdate, UserVerificationCodeRequest
from app.utils.hash_utils import hash_password, verify_password
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/users", tags=["users"])

VERIFICATION_CODE_TTL_SECONDS = 300
VERIFICATION_CODE_COOLDOWN_SECONDS = 60
VERIFICATION_CODE_MAX_ATTEMPTS = 5
_verification_code_state: dict[str, dict[str, float | int]] = {}
_verification_code_lock = threading.Lock()


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


@router.get("", dependencies=[Depends(require_admin)])
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


@router.post("", dependencies=[Depends(require_admin)])
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
    with _verification_code_lock:
        code_state = _verification_code_state.get(payload.employee_no)
        if code_state and time.monotonic() > float(code_state["expires_at"]):
            _verification_code_state.pop(payload.employee_no, None)
            raise BusinessException("验证码已过期，请重新获取", 403)
        if code_state and int(code_state["attempts"]) >= VERIFICATION_CODE_MAX_ATTEMPTS:
            raise BusinessException("验证码错误次数过多，请重新获取", 429)
    if not verify_password(payload.verification_code, user.verification_code_hash):
        if code_state:
            with _verification_code_lock:
                code_state["attempts"] = int(code_state["attempts"]) + 1
        raise BusinessException("验证码错误，请联系管理员重新获取", 403)

    user.password_hash = hash_password(payload.password)
    user.is_verified = True
    user.is_active = True
    with _verification_code_lock:
        _verification_code_state.pop(payload.employee_no, None)

    db.commit()
    db.refresh(user)
    data = _serialize_user(user)
    data["access_token"] = create_access_token(user.id, user.role)
    data["token_type"] = "bearer"
    return success_response(data, message="注册成功")


@router.post("/verification-code")
def send_registration_verification_code(payload: UserVerificationCodeRequest, db: Session = Depends(get_db_dep)):
    user = db.scalar(select(User).where(User.employee_no == payload.employee_no))
    if not user:
        raise BusinessException("工号不存在，请联系系统管理员核对员工档案", 404)
    if user.is_verified:
        raise BusinessException("该工号已完成账号激活，请直接登录", 409)
    if (user.phone or "") != payload.phone:
        raise BusinessException("手机号与工号档案不匹配", 403)

    now = time.monotonic()
    with _verification_code_lock:
        previous = _verification_code_state.get(payload.employee_no)
        if previous and now < float(previous["sent_at"]) + VERIFICATION_CODE_COOLDOWN_SECONDS:
            raise BusinessException("验证码发送过于频繁，请稍后再试", 429)

    verification_code = f"{secrets.randbelow(1_000_000):06d}"
    user.verification_code_hash = hash_password(verification_code)
    db.commit()
    with _verification_code_lock:
        _verification_code_state[payload.employee_no] = {
            "sent_at": now,
            "expires_at": now + VERIFICATION_CODE_TTL_SECONDS,
            "attempts": 0,
        }

    masked_phone = f"{payload.phone[:3]}****{payload.phone[-4:]}" if len(payload.phone) >= 7 else payload.phone
    return success_response(
        {"masked_phone": masked_phone, "verification_code": verification_code},
        message="验证码已生成",
    )


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
    data = _serialize_user(user)
    data["access_token"] = create_access_token(user.id, user.role)
    data["token_type"] = "bearer"
    return success_response(data, message="登录成功")


@router.get("/{user_id}", dependencies=[Depends(require_admin)])
def get_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    return success_response(_serialize_user(user))


@router.put("/{user_id}", dependencies=[Depends(require_admin)])
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


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    user.is_active = False
    db.commit()
    return success_response(message="deleted")
