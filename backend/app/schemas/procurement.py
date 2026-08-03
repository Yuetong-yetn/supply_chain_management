"""采购/入库相关请求模型。"""

from pydantic import BaseModel


class POItem(BaseModel):
    product_id: int; purchase_quantity: int; purchase_price: float


class POCreate(BaseModel):
    supplier_id: int; created_by: int; expected_arrival_date: str | None = None
    remark: str | None = None; items: list[POItem]


class InboundCreate(BaseModel):
    purchase_order_id: int | None = None; warehouse_id: int; handled_by: int | None = None
    remark: str | None = None


class BatchCompleteInboundRequest(BaseModel):
    ids: list[int]
