"""补货/出库相关请求模型。"""

from pydantic import BaseModel


class ReplenishCreate(BaseModel):
    store_id: int; product_id: int; request_quantity: int
    request_reason: str | None = None; created_by: int | None = None


class OutboundCreate(BaseModel):
    source_warehouse_id: int; target_store_id: int; handled_by: int | None = None
    source_request_id: int | None = None; remark: str | None = None
