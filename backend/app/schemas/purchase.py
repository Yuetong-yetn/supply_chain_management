from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import ORMBase


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    purchase_quantity: int
    purchase_price: Decimal


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    expected_arrival_date: date | None = None
    created_by: int
    remark: str | None = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderItemRead(ORMBase):
    id: int
    product_id: int
    purchase_quantity: int
    purchase_price: Decimal
    subtotal_amount: Decimal


class PurchaseOrderRead(ORMBase):
    id: int
    order_no: str
    supplier_id: int
    created_by: int
    created_at: datetime
    expected_arrival_date: date | None = None
    status: str
    total_amount: Decimal
    remark: str | None = None
    items: list[PurchaseOrderItemRead]
