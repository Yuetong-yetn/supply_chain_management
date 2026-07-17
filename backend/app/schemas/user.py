from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMBase

ROLE_ALIASES = {
    "admin": "admin",
    "buyer": "buyer",
    "purchaser": "buyer",
    "warehouse_manager": "warehouse_manager",
    "warehouse": "warehouse_manager",
    "store_staff": "store_staff",
    "store": "store_staff",
    "manager": "manager",
}

ROLE_LOCATION_TYPES = {
    "warehouse_manager": "warehouse",
    "store_staff": "store",
}


def normalize_user_role(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    if normalized not in ROLE_ALIASES:
        raise ValueError("不支持的用户角色")
    return ROLE_ALIASES[normalized]


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def normalize_employee_no(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None
    return normalized.upper()


class UserBase(BaseModel):
    username: str
    employee_no: str
    real_name: str | None = None
    role: str
    location_type: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    phone: str | None = None
    is_active: bool = True
    is_verified: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = normalize_text(value)
        if not normalized:
            raise ValueError("用户名不能为空")
        return normalized

    @field_validator("employee_no")
    @classmethod
    def validate_employee_no(cls, value: str) -> str:
        normalized = normalize_employee_no(value)
        if not normalized:
            raise ValueError("工号不能为空")
        return normalized

    @field_validator("real_name", "phone")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return normalize_text(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = normalize_user_role(value)
        if not normalized:
            raise ValueError("用户角色不能为空")
        return normalized

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, value: str | None) -> str | None:
        normalized = normalize_text(value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {"warehouse", "store"}:
            raise ValueError("location_type 仅支持 warehouse 或 store")
        return lowered

    @model_validator(mode="after")
    def apply_role_defaults(self):
        expected_location_type = ROLE_LOCATION_TYPES.get(self.role)
        if expected_location_type:
            self.location_type = expected_location_type
        elif self.location_type not in {"warehouse", "store"}:
            self.location_type = None

        if self.location_type == "warehouse":
            self.store_id = None
        elif self.location_type == "store":
            self.warehouse_id = None
        else:
            self.warehouse_id = None
            self.store_id = None
        return self


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    verification_code: str = Field(min_length=4, max_length=32)

    @field_validator("verification_code")
    @classmethod
    def validate_verification_code(cls, value: str) -> str:
        normalized = normalize_text(value)
        if not normalized:
            raise ValueError("验证码不能为空")
        return normalized


class UserRegister(BaseModel):
    employee_no: str
    real_name: str
    phone: str
    verification_code: str = Field(min_length=4, max_length=32)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("employee_no")
    @classmethod
    def validate_employee_no(cls, value: str) -> str:
        normalized = normalize_employee_no(value)
        if not normalized:
            raise ValueError("工号不能为空")
        return normalized

    @field_validator("real_name", "phone", "verification_code")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = normalize_text(value)
        if not normalized:
            raise ValueError("必填字段不能为空")
        return normalized


class UserVerificationCodeRequest(BaseModel):
    employee_no: str
    phone: str

    @field_validator("employee_no")
    @classmethod
    def validate_employee_no(cls, value: str) -> str:
        normalized = normalize_employee_no(value)
        if not normalized:
            raise ValueError("工号不能为空")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_text(value)
        if not normalized:
            raise ValueError("手机号不能为空")
        return normalized


class UserLogin(BaseModel):
    username: str
    password: str = Field(min_length=1, max_length=128)
    role: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = normalize_text(value)
        if not normalized:
            raise ValueError("登录标识不能为空")
        return normalized

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        return normalize_user_role(value)


class UserUpdate(BaseModel):
    username: str | None = None
    employee_no: str | None = None
    real_name: str | None = None
    role: str | None = None
    location_type: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    phone: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    verification_code: str | None = Field(default=None, min_length=4, max_length=32)

    @field_validator("username", "real_name", "phone", "verification_code")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return normalize_text(value)

    @field_validator("employee_no")
    @classmethod
    def validate_employee_no(cls, value: str | None) -> str | None:
        return normalize_employee_no(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        return normalize_user_role(value)

    @field_validator("location_type")
    @classmethod
    def validate_location_type(cls, value: str | None) -> str | None:
        normalized = normalize_text(value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in {"warehouse", "store"}:
            raise ValueError("location_type 仅支持 warehouse 或 store")
        return lowered


class UserIdentityRead(BaseModel):
    employee_no: str
    role: str
    location_type: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    location_name: str | None = None
    is_verified: bool


class UserRead(UserBase, ORMBase):
    id: int
    created_at: datetime
