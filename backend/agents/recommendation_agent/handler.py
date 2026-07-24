import math
from datetime import datetime
from sqlalchemy import delete, func, select
from kernel.common.database import Session
from kernel.common.event import Event, event_bus
from kernel.common.exceptions import BusinessException
from kernel.common.query_service import list_stores, get_store_inventory, get_supplier_product_by_product
from .models import AIRecommendation, MonthlySalesFact, Promotion

def generate_recommendations(db: Session, store_id: int = None, enhance_with_llm: bool = False):
    if store_id:
        db.execute(delete(AIRecommendation).where(AIRecommendation.store_id == store_id))
    else:
        db.execute(delete(AIRecommendation))
    stores = list_stores(db, store_id)
    recs = []
    latest = db.execute(select(MonthlySalesFact.year, MonthlySalesFact.month)
        .order_by(MonthlySalesFact.year.desc(), MonthlySalesFact.month.desc()).limit(1)).first()
    ly, lm = (latest.year, latest.month) if latest else (datetime.now().year, datetime.now().month)
    for store in stores:
        invs = get_store_inventory(db, store.id)
        for inv in invs:
            sales = db.scalar(select(func.coalesce(func.sum(MonthlySalesFact.retail_sales), 0))
                .where(MonthlySalesFact.store_id == store.id, MonthlySalesFact.product_id == inv.product_id,
                       MonthlySalesFact.year == ly, MonthlySalesFact.month == lm)) or 0
            avg_daily = sales / 30
            sp = get_supplier_product_by_product(db, inv.product_id)
            lead_time = sp.lead_time_days if sp else 3
            target = math.ceil(avg_daily * (lead_time + 10) + inv.safety_stock)
            qty = max(0, target - inv.current_quantity)
            promo = db.scalar(select(Promotion).where(Promotion.store_id == store.id, Promotion.product_id == inv.product_id))
            if promo: qty = math.ceil(qty * 1.2)
            days_to = inv.current_quantity / max(avg_daily, 0.01)
            risk = "high" if days_to <= lead_time else ("medium" if days_to <= lead_time + 3 else "low")
            rec = AIRecommendation(store_id=store.id, product_id=inv.product_id,
                current_stock=inv.current_quantity, recent_7_sales=sales/4, recent_30_sales=sales,
                avg_daily_sales=avg_daily, safety_stock=inv.safety_stock, recommended_quantity=qty,
                shortage_risk=risk in ("medium","high"), risk_level=risk, days_until_stockout=days_to,
                reason=f"当前库存{inv.current_quantity}，建议补货{qty}件，预计{days_to:.1f}天后缺货")
            db.add(rec); recs.append(rec)
    db.flush()
    event_bus.publish(Event(type="recommendation.generated", source="recommendation_agent", data={"count": len(recs)}))
    return recs

def set_adoption_status(db: Session, rid: int, status: str):
    r = db.get(AIRecommendation, rid)
    if not r: raise BusinessException("recommendation not found", 404)
    r.adoption_status = status; db.flush(); return r
