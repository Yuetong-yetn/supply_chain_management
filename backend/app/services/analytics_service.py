from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.models.analytics import MonthlySalesFact, SupplierScoreSnapshot
from app.models.inventory import Inventory
from app.models.outbound import OutboundItem, OutboundOrder
from app.models.product import Product
from app.models.recommendation import AIRecommendation
from app.models.store import Store
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.services.inventory_service import get_inventory_warnings
from app.services.llm.llm_router import get_llm_client
from app.services.llm.prompt_templates import analytics_summary_prompt


def cacheable(key: str, builder):
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = builder()
    cache.set(key, value)
    return value


def inventory_ranking(db: Session) -> list[dict]:
    def _builder():
        rows = db.execute(
            select(Product.name, func.sum(Inventory.current_quantity).label("qty"))
            .join(Product, Product.id == Inventory.product_id)
            .group_by(Product.id)
            .order_by(func.sum(Inventory.current_quantity).desc())
            .limit(20)
        ).all()
        return [{"product_name": name, "quantity": qty} for name, qty in rows]
    return cacheable("analytics:inventory-ranking", _builder)


def supplier_purchase_ranking(db: Session) -> list[dict]:
    def _builder():
        rows = db.execute(
            select(Supplier.name, func.coalesce(func.max(SupplierScoreSnapshot.total_purchase_amount), 0))
            .outerjoin(SupplierScoreSnapshot, SupplierScoreSnapshot.supplier_id == Supplier.id)
            .group_by(Supplier.id)
            .order_by(func.coalesce(func.max(SupplierScoreSnapshot.total_purchase_amount), 0).desc())
        ).all()
        return [{"supplier_name": name, "total_purchase_amount": float(amount)} for name, amount in rows]
    return cacheable("analytics:supplier-purchase-ranking", _builder)


def dashboard(db: Session) -> dict:
    def _builder():
        warnings = get_inventory_warnings(db)
        stockout_warnings = [w for w in warnings if w["warning_type"] in {"stockout", "critical_stockout"}]
        overstock_warnings = [w for w in warnings if w["warning_type"] == "overstock"]
        rows = db.execute(
            select(func.coalesce(func.sum(OutboundItem.quantity), 0))
            .join(OutboundOrder, OutboundOrder.id == OutboundItem.outbound_order_id)
            .where(OutboundOrder.status.in_(["shipped", "signed"]))
        ).scalar_one()
        high_risk_count = db.scalar(select(func.count(AIRecommendation.id)).where(AIRecommendation.risk_level == "high")) or 0
        total_inventory = db.scalar(select(func.coalesce(func.sum(Inventory.current_quantity), 0))) or 0
        return {
            "product_count": db.scalar(select(func.count(Product.id))) or 0,
            "supplier_count": db.scalar(select(func.count(Supplier.id))) or 0,
            "warehouse_count": db.scalar(select(func.count(Warehouse.id))) or 0,
            "store_count": db.scalar(select(func.count(Store.id))) or 0,
            "stockout_count": len([w for w in warnings if "stockout" in w["warning_type"]]),
            "overstock_count": len(overstock_warnings),
            "recent_outbound_quantity": int(rows or 0),
            "ai_recommendation_count": db.scalar(select(func.count(AIRecommendation.id))) or 0,
            "high_risk_recommendation_count": high_risk_count,
            "total_inventory_quantity": int(total_inventory),
            "top_stockout_products": stockout_warnings[:5],
            "top_overstock_products": overstock_warnings[:5],
        }
    return cacheable("analytics:dashboard", _builder)


def stockout_products(db: Session) -> list[dict]:
    return [item for item in get_inventory_warnings(db) if "stockout" in item["warning_type"]]


def overstock_products(db: Session) -> list[dict]:
    return [item for item in get_inventory_warnings(db) if item["warning_type"] == "overstock"]


def store_replenishment_frequency(db: Session) -> list[dict]:
    from app.models.replenishment import ReplenishmentRequest

    rows = db.execute(
        select(Store.name, func.count(ReplenishmentRequest.id))
        .join(ReplenishmentRequest, ReplenishmentRequest.store_id == Store.id)
        .group_by(Store.id)
        .order_by(func.count(ReplenishmentRequest.id).desc())
    ).all()
    return [{"store_name": name, "request_count": count} for name, count in rows]


def warehouse_flow_trend(db: Session) -> list[dict]:
    rows = db.execute(
        select(MonthlySalesFact.year, MonthlySalesFact.month, Warehouse.name, func.sum(MonthlySalesFact.warehouse_sales))
        .join(Warehouse, Warehouse.id == MonthlySalesFact.warehouse_id)
        .group_by(MonthlySalesFact.year, MonthlySalesFact.month, Warehouse.id)
        .order_by(MonthlySalesFact.year, MonthlySalesFact.month)
    ).all()
    return [{"year": y, "month": m, "warehouse_name": n, "warehouse_sales": s} for y, m, n, s in rows]


def product_turnover(db: Session) -> list[dict]:
    rows = db.execute(
        select(Product.name, func.avg(MonthlySalesFact.retail_sales))
        .join(Product, Product.id == MonthlySalesFact.product_id)
        .group_by(Product.id)
        .order_by(func.avg(MonthlySalesFact.retail_sales).desc())
    ).all()
    return [{"product_name": name, "avg_monthly_sales": avg} for name, avg in rows]


def store_demand_heatmap(db: Session) -> list[dict]:
    rows = db.execute(
        select(Store.name, func.sum(MonthlySalesFact.retail_sales))
        .join(Store, Store.id == MonthlySalesFact.store_id)
        .group_by(Store.id)
        .order_by(func.sum(MonthlySalesFact.retail_sales).desc())
    ).all()
    return [{"store_name": name, "retail_sales": sales} for name, sales in rows]


def summary_text(db: Session) -> dict:
    data = dashboard(db)
    client = get_llm_client()
    if client:
        try:
            text = client.generate_text(analytics_summary_prompt(data))
            return {"summary": text, "llm_used": True}
        except Exception:
            pass
    summary = (
        f"当前系统共有 {data['product_count']} 个商品、{data['supplier_count']} 个供应商，"
        f"缺货预警 {data['stockout_count']} 条，积压预警 {data['overstock_count']} 条，"
        f"高风险补货建议 {data['high_risk_recommendation_count']} 条。"
    )
    return {"summary": summary, "llm_used": False}
