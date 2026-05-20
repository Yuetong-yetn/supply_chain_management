from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.response import success_response
from app.services.analytics_service import (
    dashboard,
    inventory_ranking,
    overstock_products,
    product_turnover,
    stockout_products,
    store_demand_heatmap,
    store_replenishment_frequency,
    summary_text,
    supplier_purchase_ranking,
    warehouse_flow_trend,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/inventory-ranking")
def inventory_rank(db: Session = Depends(get_db_dep)):
    return success_response(inventory_ranking(db))


@router.get("/stockout-products")
def stockout(db: Session = Depends(get_db_dep)):
    return success_response(stockout_products(db))


@router.get("/overstock-products")
def overstock(db: Session = Depends(get_db_dep)):
    return success_response(overstock_products(db))


@router.get("/store-replenishment-frequency")
def replenishment_frequency(db: Session = Depends(get_db_dep)):
    return success_response(store_replenishment_frequency(db))


@router.get("/warehouse-flow-trend")
def flow_trend(db: Session = Depends(get_db_dep)):
    return success_response(warehouse_flow_trend(db))


@router.get("/supplier-purchase-ranking")
def supplier_rank(db: Session = Depends(get_db_dep)):
    return success_response(supplier_purchase_ranking(db))


@router.get("/product-turnover")
def turnover(db: Session = Depends(get_db_dep)):
    return success_response(product_turnover(db))


@router.get("/store-demand-heatmap")
def heatmap(db: Session = Depends(get_db_dep)):
    return success_response(store_demand_heatmap(db))


@router.get("/dashboard")
def dashboard_api(db: Session = Depends(get_db_dep)):
    return success_response(dashboard(db))


@router.get("/summary-text")
def summary_api(db: Session = Depends(get_db_dep)):
    return success_response(summary_text(db))
