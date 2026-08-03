"""供应商相关请求模型。"""

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str; contact_person: str | None = None; phone: str | None = None
    email: str | None = None; address: str | None = None; supplier_level: str | None = None


class SupplierProductBind(BaseModel):
    product_id: int
    supply_price: float | None = None
    lead_time_days: int | None = None
    on_time_rate: float | None = None
    quality_score: float | None = None
    is_preferred: bool = False
