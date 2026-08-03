"""库存相关请求模型。"""

from pydantic import BaseModel


class AdjustReq(BaseModel):
    product_id: int; location_type: str; new_quantity: int
    warehouse_id: int | None = None; store_id: int | None = None; operator_id: int | None = None; remark: str = ""
