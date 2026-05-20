from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class StoreBase(BaseModel):
    store_code: str
    name: str
    region: str | None = None
    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_person: str | None = None
    phone: str | None = None
    business_status: str = "active"
    is_synthetic: bool = False


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: str | None = None
    region: str | None = None
    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_person: str | None = None
    phone: str | None = None
    business_status: str | None = None
    is_synthetic: bool | None = None


class StoreRead(StoreBase, ORMBase):
    id: int
    created_at: datetime
