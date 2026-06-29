from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class UserBase(BaseModel):
    username: str
    real_name: str | None = None
    role: str
    location_type: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    phone: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    real_name: str | None = None
    role: str | None = None
    location_type: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    phone: str | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(UserBase, ORMBase):
    id: int
    created_at: datetime
