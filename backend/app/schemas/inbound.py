from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class InboundItemCreate(BaseModel):
    product_id: int
    quantity: int
    batch_no: str | None = None
    production_date: date | None = None
    expiry_date: date | None = None


class InboundOrderCreate(BaseModel):
    purchase_order_id: int | None = None
    supplier_id: int
    warehouse_id: int
    handled_by: int
    status: str = "pending"
    remark: str | None = None
    items: list[InboundItemCreate]


class InboundItemRead(ORMBase):
    id: int
    product_id: int
    quantity: int
    batch_no: str | None = None
    production_date: date | None = None
    expiry_date: date | None = None


class InboundOrderRead(ORMBase):
    id: int
    inbound_no: str
    purchase_order_id: int | None = None
    supplier_id: int
    warehouse_id: int
    inbound_time: datetime
    handled_by: int
    status: str
    remark: str | None = None
    items: list[InboundItemRead]
