"""后台 LLM 分析业务逻辑 — 由事件触发，不阻塞主流程。"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from kernel.common.database import Session, SessionLocal
from kernel.common.event import Event, event_bus
from kernel.common.llm_service import (
    InventoryRiskContext,
    LLMAnalysisResult,
    RestockRiskContext,
    get_llm_provider,
)
from kernel.common.query_service import get_supplier_product_by_product
from .events import EVENT_INVENTORY_WARNING_ANALYZED, EVENT_RESTOCK_RISK_ANALYZED
from .models import InventoryWarningAnalysis, RestockRiskAnalysis

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 公开入口：由 Agent 的事件订阅回调调用
# ═══════════════════════════════════════════════════════════


def on_stock_changed(event_data: dict[str, Any]) -> None:
    """库存变动事件触发后台 LLM 分析（异步执行）。

    由 EventBus 事件回调调用，内部启动数据库 Session。
    不会阻塞事件发布者的事务提交。
    """
    product_id = event_data.get("product_id")
    location_type = event_data.get("location_type")
    warehouse_id = event_data.get("warehouse_id")
    store_id = event_data.get("store_id")
    event_type = event_data.get("_event_type", "inventory.stock.changed")

    if not product_id or not location_type:
        logger.warning("[AnalysisAgent] Missing product_id or location_type in event data")
        return

    db = SessionLocal()
    try:
        _run_inventory_warning_analysis(db, product_id, location_type, warehouse_id, store_id, event_type)
        _run_restock_risk_analysis(db, product_id, store_id, event_type)
        db.commit()
        logger.info(
            "[AnalysisAgent] LLM analysis completed for product=%s, location=%s",
            product_id, location_type,
        )
    except Exception:
        db.rollback()
        logger.exception("[AnalysisAgent] LLM analysis failed for product=%s", product_id)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# 库存预警分析
# ═══════════════════════════════════════════════════════════


def _get_product_name(db: Session, product_id: int) -> str:
    from app.models.product import Product
    p = db.get(Product, product_id)
    return p.name if p else f"商品#{product_id}"


def _get_location_name(db: Session, location_type: str, warehouse_id: int | None, store_id: int | None) -> str:
    name = "未知位置"
    if location_type == "warehouse" and warehouse_id:
        from app.models.warehouse import Warehouse
        w = db.get(Warehouse, warehouse_id)
        if w:
            name = w.name
    elif location_type == "store" and store_id:
        from app.models.store import Store
        s = db.get(Store, store_id)
        if s:
            name = s.name
    return name


def _get_inventory(db: Session, product_id: int, location_type: str,
                   warehouse_id: int | None, store_id: int | None):
    from app.services.inventory_service import get_available
    from app.models.inventory import Inventory

    inv = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.location_type == location_type,
            Inventory.warehouse_id == warehouse_id,
            Inventory.store_id == store_id,
        )
    )
    if not inv:
        return None
    return inv, get_available(inv)


def _get_recent_sales(db: Session, product_id: int, location_type: str,
                      warehouse_id: int | None, store_id: int | None) -> tuple[float, float]:
    """获取近7日/30日销量用于 LLM 分析上下文"""
    from app.models.transaction import StockTransaction

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    def _location_filter(q):
        if location_type == "warehouse":
            return q.where(
                StockTransaction.target_location_type == "warehouse",
                StockTransaction.target_warehouse_id == warehouse_id,
            )
        elif location_type == "store":
            return q.where(
                StockTransaction.target_location_type == "store",
                StockTransaction.target_store_id == store_id,
            )
        return q.where(StockTransaction.product_id == product_id)

    sales_7d = db.scalar(
        _location_filter(
            select(func.coalesce(func.sum(StockTransaction.change_quantity), 0))
            .where(
                StockTransaction.product_id == product_id,
                StockTransaction.transaction_time >= seven_days_ago,
                StockTransaction.change_quantity > 0,
            )
        )
    ) or 0

    sales_30d = db.scalar(
        _location_filter(
            select(func.coalesce(func.sum(StockTransaction.change_quantity), 0))
            .where(
                StockTransaction.product_id == product_id,
                StockTransaction.transaction_time >= thirty_days_ago,
                StockTransaction.change_quantity > 0,
            )
        )
    ) or 0

    return float(sales_7d), float(sales_30d)


def _run_inventory_warning_analysis(db: Session, product_id: int, location_type: str,
                                    warehouse_id: int | None, store_id: int | None,
                                    event_type: str) -> InventoryWarningAnalysis | None:
    """对指定商品的库存进行 LLM 预警分析，结果写入 inventory_warning_analyses 表"""
    inv_data = _get_inventory(db, product_id, location_type, warehouse_id, store_id)
    if not inv_data:
        return None
    inv, available = inv_data

    product_name = _get_product_name(db, product_id)
    location_name = _get_location_name(db, location_type, warehouse_id, store_id)
    sales_7d, sales_30d = _get_recent_sales(db, product_id, location_type, warehouse_id, store_id)

    ctx = InventoryRiskContext(
        product_id=product_id,
        product_name=product_name,
        location_type=location_type,
        location_name=location_name,
        current_quantity=inv.current_quantity,
        safety_stock=inv.safety_stock,
        max_stock=inv.max_stock,
        available_quantity=available,
        recent_outbound_7d=sales_7d,
        recent_outbound_30d=sales_30d,
    )

    provider = get_llm_provider()
    result: LLMAnalysisResult = provider.analyze_inventory_risk(ctx)

    # 写入分析结果
    analysis = InventoryWarningAnalysis(
        product_id=product_id,
        location_type=location_type,
        warehouse_id=warehouse_id,
        store_id=store_id,
        current_quantity=ctx.current_quantity,
        safety_stock=ctx.safety_stock,
        max_stock=ctx.max_stock,
        available_quantity=ctx.available_quantity,
        warning_label=result.label,
        analysis_text=result.analysis,
        llm_provider=result.llm_provider,
        confidence=result.confidence,
        triggered_by_event=event_type,
        inventory_id=inv.id,
    )
    db.add(analysis)
    db.flush()

    # 发布分析完成事件（供其他 Agent 消费，如前端提醒）
    event_bus.publish(Event(
        type=EVENT_INVENTORY_WARNING_ANALYZED,
        source="analysis_agent",
        data={
            "id": analysis.id,
            "product_id": product_id,
            "location_type": location_type,
            "warning_label": result.label,
            "analysis_text": result.analysis,
            "llm_provider": result.llm_provider,
        },
    ))
    return analysis


# ═══════════════════════════════════════════════════════════
# 补货风险分析
# ═══════════════════════════════════════════════════════════


def _run_restock_risk_analysis(db: Session, product_id: int, store_id: int | None,
                               event_type: str) -> RestockRiskAnalysis | None:
    """当门店库存变动时，自动评估补货风险

    只有 location_type=store 且有 store_id 时才执行。
    """
    if not store_id:
        return None

    from app.models.inventory import Inventory
    from backend.agents.recommendation_agent.handler import generate_recommendations

    # 检查该门店此商品是否存在库存
    inv = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.location_type == "store",
            Inventory.store_id == store_id,
        )
    )
    if not inv:
        return None

    # 获取门店名
    from app.models.store import Store
    store = db.get(Store, store_id)
    store_name = store.name if store else f"门店#{store_id}"

    product_name = _get_product_name(db, product_id)

    # 获取销售数据
    avg_daily = 0.0
    recent_30_sales = 0.0
    sales_7d, sales_30d = _get_recent_sales(db, product_id, "store", None, store_id)
    if sales_30d > 0:
        avg_daily = sales_30d / 30
        recent_30_sales = sales_30d

    sp = get_supplier_product_by_product(db, product_id)
    lead_time = sp.lead_time_days if sp and hasattr(sp, 'lead_time_days') else 3

    # 计算预计缺货天数
    days_to = inv.current_quantity / max(avg_daily, 0.01)

    # 检查是否有促销活动
    from backend.agents.recommendation_agent.models import Promotion
    promo = db.scalar(
        select(Promotion).where(
            Promotion.store_id == store_id,
            Promotion.product_id == product_id,
        )
    )

    # 获取推荐补货量（简化计算，与 recommendation_agent 一致）
    target = inv.safety_stock * 2  # 简单目标库存
    recommended_qty = max(0, target - inv.current_quantity)

    ctx = RestockRiskContext(
        store_id=store_id,
        store_name=store_name,
        product_id=product_id,
        product_name=product_name,
        current_stock=inv.current_quantity,
        avg_daily_sales=avg_daily,
        safety_stock=inv.safety_stock,
        lead_time_days=lead_time,
        days_until_stockout=days_to,
        recent_30_sales=recent_30_sales,
        has_promotion=promo is not None,
        recommended_qty=recommended_qty,
    )

    provider = get_llm_provider()
    result: LLMAnalysisResult = provider.evaluate_restock_risk(ctx)

    # 写入分析结果
    analysis = RestockRiskAnalysis(
        store_id=store_id,
        product_id=product_id,
        current_stock=ctx.current_stock,
        avg_daily_sales=ctx.avg_daily_sales,
        safety_stock=ctx.safety_stock,
        lead_time_days=ctx.lead_time_days,
        days_until_stockout=ctx.days_until_stockout,
        recommended_qty=ctx.recommended_qty,
        risk_level=result.label,
        analysis_text=result.analysis,
        llm_provider=result.llm_provider,
        confidence=result.confidence,
        triggered_by_event=event_type,
    )
    db.add(analysis)
    db.flush()

    # 发布分析完成事件
    event_bus.publish(Event(
        type=EVENT_RESTOCK_RISK_ANALYZED,
        source="analysis_agent",
        data={
            "id": analysis.id,
            "store_id": store_id,
            "product_id": product_id,
            "risk_level": result.label,
            "analysis_text": result.analysis,
            "llm_provider": result.llm_provider,
        },
    ))
    return analysis


# ═══════════════════════════════════════════════════════════
# 查询接口（供 Router 使用）
# ═══════════════════════════════════════════════════════════


def get_latest_warning_analysis(db: Session, product_id: int,
                                location_type: str,
                                warehouse_id: int | None = None,
                                store_id: int | None = None,
                                limit: int = 5) -> list[dict]:
    """获取指定商品位置的最新 LLM 预警分析结果"""
    q = (
        select(InventoryWarningAnalysis)
        .where(
            InventoryWarningAnalysis.product_id == product_id,
            InventoryWarningAnalysis.location_type == location_type,
        )
        .order_by(InventoryWarningAnalysis.created_at.desc())
        .limit(limit)
    )
    if warehouse_id:
        q = q.where(InventoryWarningAnalysis.warehouse_id == warehouse_id)
    if store_id:
        q = q.where(InventoryWarningAnalysis.store_id == store_id)
    rows = db.scalars(q).all()
    return [
        {
            "id": r.id,
            "warning_label": r.warning_label,
            "analysis_text": r.analysis_text,
            "llm_provider": r.llm_provider,
            "confidence": r.confidence,
            "current_quantity": r.current_quantity,
            "safety_stock": r.safety_stock,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def get_latest_restock_risk(db: Session, store_id: int,
                            product_id: int | None = None,
                            limit: int = 10) -> list[dict]:
    """获取指定门店的最新 LLM 补货风险分析"""
    q = (
        select(RestockRiskAnalysis)
        .where(RestockRiskAnalysis.store_id == store_id)
        .order_by(RestockRiskAnalysis.created_at.desc())
        .limit(limit)
    )
    if product_id:
        q = q.where(RestockRiskAnalysis.product_id == product_id)
    rows = db.scalars(q).all()
    return [
        {
            "id": r.id,
            "store_id": r.store_id,
            "product_id": r.product_id,
            "risk_level": r.risk_level,
            "analysis_text": r.analysis_text,
            "llm_provider": r.llm_provider,
            "confidence": r.confidence,
            "current_stock": r.current_stock,
            "days_until_stockout": r.days_until_stockout,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def get_all_active_warnings(db: Session) -> list[dict]:
    """获取所有非 none 的最新预警分析，用于前端展示"""
    # 子查询：每个(product_id, location_type)的最新记录
    subq = (
        select(
            InventoryWarningAnalysis.product_id,
            InventoryWarningAnalysis.location_type,
            func.max(InventoryWarningAnalysis.created_at).label("max_created"),
        )
        .group_by(InventoryWarningAnalysis.product_id, InventoryWarningAnalysis.location_type)
        .subquery()
    )
    rows = db.execute(
        select(InventoryWarningAnalysis)
        .join(
            subq,
            (InventoryWarningAnalysis.product_id == subq.c.product_id)
            & (InventoryWarningAnalysis.location_type == subq.c.location_type)
            & (InventoryWarningAnalysis.created_at == subq.c.max_created),
        )
        .where(InventoryWarningAnalysis.warning_label != "none")
        .order_by(InventoryWarningAnalysis.created_at.desc())
    ).scalars().all()

    return [
        {
            "id": r.id,
            "product_id": r.product_id,
            "product_name": _get_product_name(db, r.product_id),
            "location_type": r.location_type,
            "location_name": _get_location_name(db, r.location_type, r.warehouse_id, r.store_id),
            "warning_label": r.warning_label,
            "analysis_text": r.analysis_text,
            "llm_provider": r.llm_provider,
            "current_quantity": r.current_quantity,
            "safety_stock": r.safety_stock,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows if r.warning_label != "none"
    ]
