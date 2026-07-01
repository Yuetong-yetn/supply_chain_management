from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead, UserUpdate
from app.utils.hash_utils import hash_password, verify_password
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(User)
    if keyword:
        query = query.where(or_(User.username.contains(keyword), User.real_name.contains(keyword)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [
        UserRead.model_validate(item).model_dump()
        for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))
    ]
    return page_response(items, total, page, page_size)


@router.post("")
def create_user(payload: UserCreate, db: Session = Depends(get_db_dep)):
    user = User(**payload.model_dump(exclude={"password"}), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(UserRead.model_validate(user).model_dump())


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db_dep)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise BusinessException("用户名或密码错误", 401)
    if not user.is_active:
        raise BusinessException("该账号已停用", 403)
    if payload.role and payload.role != user.role:
        raise BusinessException("所选角色与账号身份不匹配", 403)
    return success_response(
        UserRead.model_validate(user).model_dump(),
        message="登录成功",
    )


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    return success_response(UserRead.model_validate(user).model_dump())


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    for key, value in payload.model_dump(exclude_unset=True, exclude={"password"}).items():
        setattr(user, key, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return success_response(UserRead.model_validate(user).model_dump())


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db_dep)):
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("user not found", 404)
    user.is_active = False
    db.commit()
    return success_response(message="deleted")
