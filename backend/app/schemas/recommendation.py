from datetime import datetime

from app.schemas.common import ORMBase


class RecommendationRead(ORMBase):
    id: int
    store_id: int
    product_id: int
    current_stock: int
    recent_7_sales: float
    recent_30_sales: float
    avg_daily_sales: float
    safety_stock: int
    recommended_quantity: int
    recommended_supplier_id: int | None = None
    shortage_risk: bool
    risk_level: str
    days_until_stockout: float
    reason: str
    reason_enhanced: str | None = None
    llm_provider: str
    llm_used: bool
    generated_at: datetime
    adoption_status: str
