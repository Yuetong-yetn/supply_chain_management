from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.core.database import get_db
from app.core.exceptions import BusinessException
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials) if credentials and credentials.scheme.lower() == "bearer" else None
    user = db.get(User, payload.get("user_id")) if payload else None
    if not user or not user.is_active or not user.is_verified or user.role != payload.get("role"):
        raise BusinessException("请先登录或重新登录", 401)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise BusinessException("当前账号无权执行此操作", 403)
    return user
