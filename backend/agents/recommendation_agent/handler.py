import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from sqlalchemy import delete, func, select

from kernel.common.database import Session
from kernel.common.event import Event, event_bus
from kernel.common.exceptions import BusinessException
from kernel.common.llm_service import ReasonEnhanceContext, RestockRiskContext, get_llm_provider
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
            # 规则计算的临时风险等级（LLM 增强时会被覆盖）
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

            db.add(rec)
            recs.append(rec)

    # LLM 风险等级 + 增强理由 — 批量并发调用
    if provider and provider.name != "rule" and recs:
        _batch_evaluate_risk_and_enhance(db, provider, recs, stores)

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


def _batch_evaluate_risk_and_enhance(db: Session, provider, recs: list, stores_map: list):
    """使用线程池批量并发调用 LLM 进行风险等级评估 + 补货理由增强。

    每一条补货建议会先后调用两个 LLM 方法：
      1. evaluate_restock_risk  → 计算 risk_level 和 shortage_risk
      2. enhance_reason        → 生成增强理由文本 reason_enhanced

    失败时保留规则计算的 risk_level 作为降级方案。
    """
    product_names_cache = {}

    def _get_name(pid: int) -> str:
        if pid not in product_names_cache:
            product_names_cache[pid] = _get_product_name(db, pid)
        return product_names_cache[pid]

    def _store_name(sid: int) -> str:
        for s in stores_map:
            if s.id == sid:
                return s.name if hasattr(s, 'name') else f"门店#{sid}"
        return f"门店#{sid}"

    def _process_one(rec: AIRecommendation):
        product_name = _get_name(rec.product_id)
        store_name = _store_name(rec.store_id)

        # 1) LLM 评估补货风险等级
        risk_ctx = RestockRiskContext(
            store_id=rec.store_id,
            store_name=store_name,
            product_id=rec.product_id,
            product_name=product_name,
            current_stock=rec.current_stock,
            avg_daily_sales=rec.avg_daily_sales,
            safety_stock=rec.safety_stock,
            lead_time_days=0,
            days_until_stockout=rec.days_until_stockout,
            recent_30_sales=rec.recent_30_sales,
            has_promotion=False,
            recommended_qty=rec.recommended_quantity,
        )
        risk_provider = get_llm_provider()
        risk_result = risk_provider.evaluate_restock_risk(risk_ctx)
        risk_level = risk_result.label if risk_result and risk_result.label in ("high", "medium", "low") else rec.risk_level

        # 2) LLM 增强补货理由
        reason_ctx = ReasonEnhanceContext(
            product_name=product_name,
            store_name=store_name,
            current_stock=rec.current_stock,
            avg_daily_sales=rec.avg_daily_sales,
            safety_stock=rec.safety_stock,
            recommended_qty=rec.recommended_quantity,
            risk_level=risk_level,
            days_until_stockout=rec.days_until_stockout,
            lead_time_days=0,
            has_promotion=False,
            recent_30_sales=rec.recent_30_sales,
            original_reason=rec.reason,
        )
        reason_result = provider.enhance_reason(reason_ctx)

        return rec, risk_level, reason_result

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(_process_one, rec) for rec in recs]
        for future in as_completed(futures):
            try:
                rec, risk_level, reason_result = future.result()
                rec.risk_level = risk_level
                rec.shortage_risk = risk_level in ("medium", "high")
                rec.reason_enhanced = reason_result.analysis
                rec.llm_provider = reason_result.llm_provider
                rec.llm_used = True
                logger.debug(
                    "[Recommendation] LLM processed store=%s product=%s risk=%s",
                    rec.store_id, rec.product_id, risk_level,
                )
            except Exception as e:
                logger.warning(
                    "[Recommendation] LLM evaluate+enhance failed for a recommendation: %s", e,
                )
