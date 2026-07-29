import logging
import math
from datetime import datetime

from sqlalchemy import delete, func, select

from kernel.common.database import Session
from kernel.common.event import Event, event_bus
from kernel.common.exceptions import BusinessException
from kernel.common.llm_service import ReasonEnhanceContext, get_llm_provider
from kernel.common.query_service import list_stores, get_store_inventory, get_supplier_product_by_product
from .models import AIRecommendation, MonthlySalesFact, Promotion

logger = logging.getLogger(__name__)


def generate_recommendations(db: Session, store_id: int = None, enhance_with_llm: bool = False):
    """生成 AI 补货建议。

    enhance_with_llm=True 时，在生成每条建议后调用 LLM 增强 reason_enhanced 字段。
    """
    if store_id:
        db.execute(delete(AIRecommendation).where(AIRecommendation.store_id == store_id))
    else:
        db.execute(delete(AIRecommendation))

    stores = list_stores(db, store_id)
    recs = []
    latest = db.execute(
        select(MonthlySalesFact.year, MonthlySalesFact.month)
        .order_by(MonthlySalesFact.year.desc(), MonthlySalesFact.month.desc())
        .limit(1)
    ).first()
    ly, lm = (latest.year, latest.month) if latest else (datetime.now().year, datetime.now().month)

    if enhance_with_llm:
        provider = get_llm_provider()
    else:
        provider = None

    for store in stores:
        store_name = store.name if hasattr(store, 'name') else f"门店#{store.id}"
        invs = get_store_inventory(db, store.id)
        for inv in invs:
            sales = db.scalar(
                select(func.coalesce(func.sum(MonthlySalesFact.retail_sales), 0))
                .where(
                    MonthlySalesFact.store_id == store.id,
                    MonthlySalesFact.product_id == inv.product_id,
                    MonthlySalesFact.year == ly,
                    MonthlySalesFact.month == lm,
                )
            ) or 0
            avg_daily = sales / 30
            sp = get_supplier_product_by_product(db, inv.product_id)
            lead_time = sp.lead_time_days if sp else 3
            target = math.ceil(avg_daily * (lead_time + 10) + inv.safety_stock)
            qty = max(0, target - inv.current_quantity)
            promo = db.scalar(
                select(Promotion).where(
                    Promotion.store_id == store.id, Promotion.product_id == inv.product_id,
                )
            )
            if promo:
                qty = math.ceil(qty * 1.2)
            days_to = inv.current_quantity / max(avg_daily, 0.01)
            risk = "high" if days_to <= lead_time else ("medium" if days_to <= lead_time + 3 else "low")

            reason = (
                f"当前库存{inv.current_quantity}，建议补货{qty}件，"
                f"预计{days_to:.1f}天后缺货"
            )

            rec = AIRecommendation(
                store_id=store.id,
                product_id=inv.product_id,
                current_stock=inv.current_quantity,
                recent_7_sales=sales / 4,
                recent_30_sales=sales,
                avg_daily_sales=avg_daily,
                safety_stock=inv.safety_stock,
                recommended_quantity=qty,
                shortage_risk=risk in ("medium", "high"),
                risk_level=risk,
                days_until_stockout=days_to,
                reason=reason,
            )

            # LLM 增强理由
            if provider and provider.name != "rule":
                product_name = _get_product_name(db, inv.product_id)
                ctx = ReasonEnhanceContext(
                    product_name=product_name,
                    store_name=store_name,
                    current_stock=inv.current_quantity,
                    avg_daily_sales=avg_daily,
                    safety_stock=inv.safety_stock,
                    recommended_qty=qty,
                    risk_level=risk,
                    days_until_stockout=days_to,
                    lead_time_days=lead_time,
                    has_promotion=promo is not None,
                    recent_30_sales=sales,
                    original_reason=reason,
                )
                try:
                    result = provider.enhance_reason(ctx)
                    rec.reason_enhanced = result.analysis
                    rec.llm_provider = result.llm_provider
                    rec.llm_used = True
                except Exception as e:
                    logger.warning(
                        "[Recommendation] LLM enhance failed for store=%s product=%s: %s",
                        store.id, inv.product_id, e,
                    )
                    rec.llm_provider = "rule"
                    rec.llm_used = False

            db.add(rec)
            recs.append(rec)

    db.flush()
    event_bus.publish(Event(
        type="recommendation.generated",
        source="recommendation_agent",
        data={"count": len(recs)},
    ))
    logger.info(
        "[Recommendation] Generated %d recommendations (enhance_with_llm=%s)",
        len(recs), enhance_with_llm,
    )
    return recs


def set_adoption_status(db: Session, rid: int, status: str):
    r = db.get(AIRecommendation, rid)
    if not r:
        raise BusinessException("recommendation not found", 404)
    r.adoption_status = status
    db.flush()
    return r


def _get_product_name(db: Session, product_id: int) -> str:
    """获取商品名称（延迟加载避免循环 import）。"""
    from agents.product_agent.models import Product
    p = db.get(Product, product_id)
    return p.name if p else f"商品#{product_id}"
