"""用户/认证相关请求模型。"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class VerificationCodeRequest(BaseModel):
    employee_no: str
    phone: str


class RegisterRequest(BaseModel):
    employee_no: str
    real_name: str
    phone: str
    verification_code: str
    password: str
