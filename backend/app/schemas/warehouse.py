from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class WarehouseBase(BaseModel):
    warehouse_code: str
    name: str
    address: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    max_capacity: int | None = None
    status: str = "active"
    region: str | None = None
    is_synthetic: bool = False


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    max_capacity: int | None = None
    status: str | None = None
    region: str | None = None
    is_synthetic: bool | None = None


class WarehouseRead(WarehouseBase, ORMBase):
    id: int
    created_at: datetime
