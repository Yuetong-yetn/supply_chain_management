from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class OutboundItemCreate(BaseModel):
    product_id: int
    quantity: int
    batch_no: str | None = None


class OutboundOrderCreate(BaseModel):
    source_warehouse_id: int
    target_store_id: int
    handled_by: int
    source_request_id: int | None = None
    remark: str | None = None
    items: list[OutboundItemCreate]


class OutboundItemRead(ORMBase):
    id: int
    product_id: int
    quantity: int
    batch_no: str | None = None


class OutboundOrderRead(ORMBase):
    id: int
    outbound_no: str
    source_warehouse_id: int
    target_store_id: int
    outbound_time: datetime
    handled_by: int
    status: str
    source_request_id: int | None = None
    remark: str | None = None
    items: list[OutboundItemRead]
