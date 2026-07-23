from fastapi import APIRouter, Depends
from kernel.common.database import get_db, Session
from kernel.common.response import success_response
from kernel.common.auth import get_current_user
from kernel.common.query_service import (
    get_basic_counts,
    get_high_risk_recommendation_count,
    get_inventory_ranking,
    get_inventory_summary,
    get_inventory_warnings,
    get_recent_outbound_quantity,
    get_warehouse_flow_trend,
)
from agents.user_agent.models import User

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    counts = get_basic_counts(db)
    warnings = get_inventory_warnings(db)
    stockout = [w for w in warnings if "stockout" in w["warning_type"]]
    overstock = [w for w in warnings if w["warning_type"] == "overstock"]

    return success_response({
        "product_count": counts["product_count"],
        "supplier_count": counts["supplier_count"],
        "warehouse_count": counts["warehouse_count"],
        "store_count": counts["store_count"],
        "stockout_count": len(stockout),
        "overstock_count": len(overstock),
        "ai_recommendation_count": counts["ai_recommendation_count"],
        "high_risk_recommendation_count": get_high_risk_recommendation_count(db),
        "total_inventory_quantity": get_inventory_summary(db)["total_inventory_quantity"],
        "recent_outbound_quantity": get_recent_outbound_quantity(db),
        "top_stockout_products": stockout[:5],
        "top_overstock_products": overstock[:5],
    })


@router.get("/analytics/summary-text")
def summary_text(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = dashboard(db)["data"]
    return success_response({
        "summary": f"当前系统共有 {d['product_count']} 个商品、{d['supplier_count']} 个供应商，"
                   f"缺货预警 {d['stockout_count']} 条，积压预警 {d['overstock_count']} 条。",
        "llm_used": False,
    })


@router.get("/analytics/inventory-ranking")
def inv_ranking(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_inventory_ranking(db))


@router.get("/analytics/stockout-products")
def stockout_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response([w for w in get_inventory_warnings(db) if "stockout" in w["warning_type"]])


@router.get("/analytics/overstock-products")
def overstock_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response([w for w in get_inventory_warnings(db) if w["warning_type"] == "overstock"])


@router.get("/analytics/warehouse-flow-trend")
def warehouse_flow_trend(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_warehouse_flow_trend(db))
