"""用户认证业务逻辑。

职责：登录验证、身份查询。
Router 层负责 HTTP 参数校验和响应封装，handler 层负责具体业务逻辑。
"""

import logging

from sqlalchemy import or_, select

from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from kernel.common.auth import create_access_token
from .models import User

logger = logging.getLogger(__name__)


def login(db: Session, username: str, password: str) -> dict:
    """验证用户名密码，返回用户信息和 token。"""
    from kernel.common.hash_utils import verify_password

    normalized_username = username.strip()
    normalized_employee_no = normalized_username.upper()
    user = db.scalar(
        select(User).where(
            or_(
                User.username == normalized_username,
                User.employee_no == normalized_employee_no,
            )
        )
    )
    if not user:
        logger.warning("Login failed: unknown username or employee_no %s", normalized_username)
        raise BusinessException("用户名或密码错误", 401)
    if not verify_password(password, user.password_hash):
        logger.warning("Login failed: wrong password for %s", normalized_username)
        raise BusinessException("用户名或密码错误", 401)
    if not user.is_active:
        raise BusinessException("用户已被禁用")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "role": user.role,
        "location_type": user.location_type,
        "warehouse_id": user.warehouse_id,
        "store_id": user.store_id,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": str(user.created_at),
        "access_token": token,
        "token_type": "bearer",
    }


def get_user_profile(db: Session, user_id: int) -> dict:
    """获取用户信息（不含敏感字段）。"""
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise BusinessException("用户不存在或已禁用")
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "role": user.role,
        "location_type": user.location_type,
        "warehouse_id": user.warehouse_id,
        "store_id": user.store_id,
        "phone": user.phone,
        "is_active": user.is_active,
    }


def list_users(db: Session, page: int = 1, page_size: int = 200) -> dict:
    """分页获取用户列表。"""
    from sqlalchemy import func, select

    total = db.scalar(select(func.count(User.id))) or 0
    rows = db.scalars(
        select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [
        {
            "id": u.id, "username": u.username, "employee_no": u.employee_no,
            "real_name": u.real_name, "role": u.role,
            "location_type": u.location_type, "warehouse_id": u.warehouse_id,
            "store_id": u.store_id, "phone": u.phone,
            "is_active": u.is_active, "is_verified": u.is_verified,
        }
        for u in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_identity_by_employee_no(db: Session, employee_no: str) -> dict:
    """根据工号查询用户身份（用于注册页面的身份识别）。"""
    user = db.scalar(select(User).where(User.employee_no == employee_no))
    if not user:
        raise BusinessException("未找到该工号对应的用户")
    # 获取关联的位置名称
    location_name = None
    if user.location_type == "warehouse" and user.warehouse_id:
        from agents.warehouse_agent.models import Warehouse
        wh = db.get(Warehouse, user.warehouse_id)
        location_name = wh.name if wh else None
    elif user.location_type == "store" and user.store_id:
        from agents.store_agent.models import Store
        st = db.get(Store, user.store_id)
        location_name = st.name if st else None
    return {
        "id": user.id, "username": user.username, "employee_no": user.employee_no,
        "real_name": user.real_name, "role": user.role,
        "location_type": user.location_type, "warehouse_id": user.warehouse_id,
        "store_id": user.store_id, "location_name": location_name,
        "phone": user.phone, "is_active": user.is_active, "is_verified": user.is_verified,
    }


def register_user(
    db: Session, employee_no: str, real_name: str, phone: str,
    verification_code: str, password: str,
) -> dict:
    """用户注册/激活：验证码校验 + 密码设置。"""
    from kernel.common.hash_utils import hash_password, verify_password

    user = db.scalar(select(User).where(User.employee_no == employee_no))
    if not user:
        raise BusinessException("未找到该工号对应的用户，请联系管理员")
    if user.is_verified:
        raise BusinessException("该工号已激活，请直接登录")
    if not verify_password(verification_code, user.verification_code_hash):
        raise BusinessException("验证码错误")
    user.password_hash = hash_password(password)
    user.real_name = real_name
    user.phone = phone
    user.is_verified = True
    db.flush()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {
        "id": user.id, "username": user.username, "employee_no": user.employee_no,
        "real_name": user.real_name, "role": user.role,
        "location_type": user.location_type, "warehouse_id": user.warehouse_id,
        "store_id": user.store_id, "phone": user.phone,
        "is_active": user.is_active, "is_verified": user.is_verified,
        "access_token": token, "token_type": "bearer",
    }
