from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class ReplenishmentRequestCreate(BaseModel):
    store_id: int
    product_id: int
    request_quantity: int
    request_reason: str | None = None
    created_by: int | None = None


class ReplenishmentRequestRead(ORMBase):
    id: int
    request_no: str
    store_id: int
    product_id: int
    request_quantity: int
    request_reason: str | None = None
    request_time: datetime
    audit_status: str
    audited_by: int | None = None
    audit_time: datetime | None = None
    created_by: int | None = None
    generated_outbound_order_id: int | None = None
