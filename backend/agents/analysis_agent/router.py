"""AI 分析结果查询路由 — 供前端展示 LLM 自动分析结论。"""

from fastapi import APIRouter, Depends, Query
from kernel.common.auth import get_current_user
from kernel.common.database import get_db, Session
from kernel.common.response import success_response
from agents.user_agent.models import User
from .handler import (
    get_all_active_warnings,
    get_latest_restock_risk,
    get_latest_warning_analysis,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/warnings")
def list_active_warnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有活跃的 LLM 预警分析（非 none 状态，按最新排序）"""
    return success_response(get_all_active_warnings(db))


@router.get("/warnings/{product_id}")
def product_warning_history(
    product_id: int,
    location_type: str = Query("warehouse"),
    warehouse_id: int = Query(None),
    store_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定商品位置的历史 LLM 预警分析"""
    return success_response(
        get_latest_warning_analysis(db, product_id, location_type, warehouse_id, store_id)
    )


@router.get("/restock-risk/{store_id}")
def store_restock_risk(
    store_id: int,
    product_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定门店的最新 LLM 补货风险分析"""
    return success_response(
        get_latest_restock_risk(db, store_id, product_id)
    )
