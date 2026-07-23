from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import get_warnings, get_summary, adjust_stock
from .models import Inventory

router = APIRouter(prefix="/api", tags=["inventory"])

@router.get("/inventory")
def list_inv(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = list(db.scalars(select(Inventory).offset((page-1)*page_size).limit(page_size)))
    total = db.scalar(select(func.count(Inventory.id))) or 0
    return page_response(items, total, page, page_size)

@router.get("/inventory/product/{pid}/distribution")
def distribution(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = list(db.scalars(select(Inventory).where(Inventory.product_id == pid)))
    return success_response(items)

@router.get("/inventory/store/{sid}")
def store_inv(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = list(db.scalars(select(Inventory).where(Inventory.store_id == sid)))
    return success_response(items)

@router.get("/inventory/warehouse/{wid}")
def wh_inv(wid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = list(db.scalars(select(Inventory).where(Inventory.warehouse_id == wid)))
    return success_response(items)

@router.get("/inventory/warnings")
def warnings_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_warnings(db))

@router.get("/inventory/summary")
def summary_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_summary(db))

class AdjustReq(BaseModel):
    product_id: int; location_type: str; new_quantity: int
    warehouse_id: int | None = None; store_id: int | None = None; operator_id: int | None = None; remark: str = ""

@router.post("/inventory/adjust")
def adjust_route(data: AdjustReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(adjust_stock(db, **data.model_dump()))
