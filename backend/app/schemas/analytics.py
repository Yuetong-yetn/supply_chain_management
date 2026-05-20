from pydantic import BaseModel


class DashboardSummary(BaseModel):
    product_count: int
    supplier_count: int
    warehouse_count: int
    store_count: int
    stockout_count: int
    overstock_count: int
    recent_outbound_quantity: int
    ai_recommendation_count: int
    high_risk_recommendation_count: int
    total_inventory_quantity: int
    top_stockout_products: list[dict]
    top_overstock_products: list[dict]
