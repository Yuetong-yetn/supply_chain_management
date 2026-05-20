from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class InventoryRead(ORMBase):
    id: int
    product_id: int
    location_type: str
    warehouse_id: int | None = None
    store_id: int | None = None
    current_quantity: int
    frozen_quantity: int
    safety_stock: int
    max_stock: int
    last_updated_at: datetime


class InventoryAdjustRequest(BaseModel):
    product_id: int
    location_type: str
    warehouse_id: int | None = None
    store_id: int | None = None
    new_quantity: int
    operator_id: int | None = None
    remark: str | None = None


class CrossWarehouseTransferCreate(BaseModel):
    source_warehouse_id: int
    target_warehouse_id: int
    product_id: int
    quantity: int
    reason: str | None = None
    created_by: int | None = None
