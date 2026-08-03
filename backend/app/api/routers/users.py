import secrets

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.core.database import get_db, Session
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.core.auth import get_current_user
from app.utils.hash_utils import hash_password
from app.schemas.users import LoginRequest, VerificationCodeRequest, RegisterRequest
from app.services.user_service import login as handler_login, get_user_profile, list_users, get_identity_by_employee_no, register_user
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    result = handler_login(db, req.username, req.password)
    return success_response(result, message="登录成功")


@router.post("/verification-code")
def send_verification_code(req: VerificationCodeRequest, db: Session = Depends(get_db)):
    from app.core.config import get_settings

    user = db.scalar(select(User).where(
        User.employee_no == req.employee_no, User.phone == req.phone
    ))
    if not user:
        raise BusinessException("工号或手机号不匹配")
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.verification_code_hash = hash_password(code)
    db.flush()
    settings = get_settings()
    response_data = {"masked_phone": req.phone[:3] + "****" + req.phone[-4:]}
    if settings.app_env == "dev":
        response_data["verification_code"] = code
    return success_response(response_data)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success_response({
        "id": current_user.id, "username": current_user.username,
        "real_name": current_user.real_name, "role": current_user.role,
        "location_type": current_user.location_type,
        "warehouse_id": current_user.warehouse_id,
        "store_id": current_user.store_id,
        "phone": current_user.phone, "is_active": current_user.is_active,
    })


@router.get("")
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    result = list_users(db, page=page, page_size=page_size)
    return success_response(result)


@router.get("/identity/{employee_no}")
def get_identity(employee_no: str, db: Session = Depends(get_db)):
    result = get_identity_by_employee_no(db, employee_no.upper())
    return success_response(result)


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    result = register_user(
        db, req.employee_no.upper(), req.real_name, req.phone,
        req.verification_code, req.password,
    )
    return success_response(result, message="注册成功")
