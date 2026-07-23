"""共享查询服务 — 避免各 Agent 直接 import 其他 Agent 的 models。

所有导入都在函数内部进行（延迟加载），避免模块级循环依赖。
"""

from sqlalchemy import func, select

from kernel.common.database import Session


def get_basic_counts(db: Session) -> dict[str, int]:
    """获取基础数据计数，用于看板首页等场景。"""
    from agents.product_agent.models import Product
    from agents.supplier_agent.models import Supplier
    from agents.warehouse_agent.models import Warehouse
    from agents.store_agent.models import Store
    from agents.inventory_agent.models import Inventory
    from agents.recommendation_agent.models import AIRecommendation

    return {
        "product_count": db.scalar(select(func.count(Product.id))) or 0,
        "supplier_count": db.scalar(select(func.count(Supplier.id))) or 0,
        "warehouse_count": db.scalar(select(func.count(Warehouse.id))) or 0,
        "store_count": db.scalar(select(func.count(Store.id))) or 0,
        "inventory_count": db.scalar(select(func.count(Inventory.id))) or 0,
        "ai_recommendation_count": db.scalar(select(func.count(AIRecommendation.id))) or 0,
    }


def get_inventory_summary(db: Session) -> dict:
    """获取库存汇总信息。"""
    from agents.inventory_agent.models import Inventory

    total_qty = db.scalar(select(func.coalesce(func.sum(Inventory.current_quantity), 0))) or 0
    return {"total_inventory_quantity": total_qty}


def get_inventory_warnings(db: Session) -> list[dict]:
    """获取库存预警列表，用于只读统计场景。"""
    from agents.inventory_agent.handler import get_warnings

    return get_warnings(db)


def get_recent_outbound_quantity(db: Session) -> int:
    """获取最近 30 天已出库/签收的出库数量。"""
    from datetime import datetime, timedelta

    from agents.fulfillment_agent.models import OutboundItem, OutboundOrder

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    return db.scalar(
        select(func.coalesce(func.sum(OutboundItem.quantity), 0))
        .join(OutboundOrder, OutboundOrder.id == OutboundItem.outbound_order_id)
        .where(OutboundOrder.outbound_time >= thirty_days_ago, OutboundOrder.status.in_(["shipped", "signed"]))
    ) or 0


def get_high_risk_recommendation_count(db: Session) -> int:
    """获取高风险推荐数量。"""
    from agents.recommendation_agent.models import AIRecommendation

    return db.scalar(select(func.count(AIRecommendation.id)).where(AIRecommendation.risk_level == "high")) or 0


def get_inventory_ranking(db: Session) -> list[dict]:
    """按库存数量返回商品排行。"""
    from agents.inventory_agent.models import Inventory
    from agents.product_agent.models import Product

    rows = db.execute(
        select(Product.name, func.sum(Inventory.current_quantity).label("qty"))
        .join(Product, Product.id == Inventory.product_id)
        .group_by(Product.id)
        .order_by(func.sum(Inventory.current_quantity).desc())
        .limit(20)
    ).all()
    return [{"product_name": name, "quantity": qty} for name, qty in rows]


def get_warehouse_flow_trend(db: Session) -> list[dict]:
    """获取仓库流量趋势。"""
    from agents.recommendation_agent.models import MonthlySalesFact
    from agents.warehouse_agent.models import Warehouse

    rows = db.execute(
        select(
            MonthlySalesFact.year,
            MonthlySalesFact.month,
            Warehouse.name,
            func.sum(MonthlySalesFact.warehouse_sales).label("warehouse_sales"),
        )
        .join(Warehouse, Warehouse.id == MonthlySalesFact.warehouse_id, isouter=True)
        .group_by(MonthlySalesFact.year, MonthlySalesFact.month, Warehouse.name)
        .order_by(MonthlySalesFact.year, MonthlySalesFact.month)
        .limit(50)
    ).all()
    return [
        {"year": year, "month": month, "warehouse_name": name or "未知仓库", "warehouse_sales": sales}
        for year, month, name, sales in rows
    ]
