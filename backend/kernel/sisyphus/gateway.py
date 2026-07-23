"""API 网关 — URL 路径到 Agent 的映射表。"""

ROUTE_MAP = {
    "users": "user_agent",
    "categories": "product_agent",
    "products": "product_agent",
    "suppliers": "supplier_agent",
    "purchase-orders": "procurement_agent",
    "inbound-orders": "procurement_agent",
    "inventory": "inventory_agent",
    "warehouses": "warehouse_agent",
    "stores": "store_agent",
    "outbound-orders": "fulfillment_agent",
    "replenishment-requests": "fulfillment_agent",
    "transactions": "transaction_agent",
    "analytics": "analytics_agent",
    "recommendations": "recommendation_agent",
    "health": "monitoring_agent",
    "example": "monitoring_agent",
    "llm": "monitoring_agent",
}
