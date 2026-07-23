from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import list_suppliers, create_supplier, get_supplier, get_supplier_products, get_ranking, get_supplier_score, recalculate_scores, bind_supplier_product

router = APIRouter(prefix="/api", tags=["suppliers"])

class SupplierCreate(BaseModel):
    name: str; contact_person: str | None = None; phone: str | None = None
    email: str | None = None; address: str | None = None; supplier_level: str | None = None


class SupplierProductBind(BaseModel):
    product_id: int
    supply_price: float | None = None
    lead_time_days: int | None = None
    on_time_rate: float | None = None
    quality_score: float | None = None
    is_preferred: bool = False

@router.get("/suppliers")
def list_route(page: int = Query(1), page_size: int = Query(20), keyword: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total = list_suppliers(db, page, page_size, keyword)
    return page_response(items, total, page, page_size)

@router.post("/suppliers")
def create_route(data: SupplierCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_supplier(db, data.model_dump()))

@router.get("/suppliers/ranking")
def ranking_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_ranking(db))

@router.post("/suppliers/recalculate-scores")
def recalc_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    snaps = recalculate_scores(db)
    return success_response({"count": len(snaps)})

@router.get("/suppliers/{sid}")
def get_route(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_supplier(db, sid))

@router.get("/suppliers/{sid}/products")
def products_route(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_supplier_products(db, sid))


@router.post("/suppliers/{sid}/products")
def bind_product_route(sid: int, data: SupplierProductBind, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(bind_supplier_product(db, sid, data.model_dump()))

@router.get("/suppliers/{sid}/score")
def score_route(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_supplier_score(db, sid))
