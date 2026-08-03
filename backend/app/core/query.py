"""共享查询服务 — 转发 kernel.common.query_service。"""

from kernel.common.query_service import (
    get_basic_counts, get_inventory_summary, get_recent_outbound_quantity,
    get_high_risk_recommendation_count, get_inventory_ranking,
    get_warehouse_flow_trend, list_stores, get_store_inventory,
    get_supplier_product_by_product, find_warehouse_with_available_stock,
)

__all__ = [
    "get_basic_counts", "get_inventory_summary", "get_recent_outbound_quantity",
    "get_high_risk_recommendation_count", "get_inventory_ranking",
    "get_warehouse_flow_trend", "list_stores", "get_store_inventory",
    "get_supplier_product_by_product", "find_warehouse_with_available_stock",
]
