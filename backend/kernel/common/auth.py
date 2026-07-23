"""JWT 认证工具。"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from kernel.common.config import get_settings
from kernel.common.database import get_db, Session
from kernel.common.exceptions import BusinessException

settings = get_settings()
ALGORITHM = "HS256"
SECRET_KEY = settings.auth_secret_key_value
TOKEN_TTL = settings.auth_token_ttl_seconds

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_TTL)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """FastAPI 依赖项：从 Bearer token 解析当前用户。

    在所有需要认证的业务路由中使用：Depends(get_current_user)
    """
    if credentials is None:
        raise BusinessException("请先登录", 401)
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise BusinessException("登录已过期，请重新登录", 401)

    from agents.user_agent.models import User

    user = db.get(User, payload.get("user_id"))
    if not user or not user.is_active:
        raise BusinessException("用户不存在或已禁用", 401)
    return user
