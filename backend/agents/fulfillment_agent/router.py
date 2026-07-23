from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from sqlalchemy import func, select
from .handler import create_request, approve_request, reject_request, convert_to_outbound, generate_no, ship_order, sign_order, cancel_order
from .models import ReplenishmentRequest, OutboundOrder

router = APIRouter(prefix="/api", tags=["fulfillment"])

class ReplenishCreate(BaseModel):
    store_id: int; product_id: int; request_quantity: int
    request_reason: str | None = None; created_by: int | None = None


class OutboundCreate(BaseModel):
    source_warehouse_id: int; target_store_id: int; handled_by: int | None = None
    source_request_id: int | None = None; remark: str | None = None


@router.post("/replenishment-requests")
def create_req(data: ReplenishCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_request(db, data.model_dump()))

@router.get("/replenishment-requests")
def list_req(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.scalar(select(func.count(ReplenishmentRequest.id))) or 0
    items = list(db.scalars(select(ReplenishmentRequest).offset((page-1)*page_size).limit(page_size)))
    return page_response(items, total, page, page_size)

@router.get("/replenishment-requests/{rid}")
def get_req(rid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(db.get(ReplenishmentRequest, rid))

@router.post("/replenishment-requests/{rid}/approve")
def approve_req(rid: int, audited_by: int = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(approve_request(db, rid, audited_by))

@router.post("/replenishment-requests/{rid}/reject")
def reject_req(rid: int, audited_by: int = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(reject_request(db, rid, audited_by))

@router.post("/replenishment-requests/{rid}/convert-to-outbound")
def convert_req(rid: int, source_warehouse_id: int | None = Query(None), handled_by: int = Query(1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(convert_to_outbound(db, rid, source_warehouse_id, handled_by))

@router.post("/outbound-orders")
def create_outbound(data: OutboundCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = OutboundOrder(outbound_no=generate_no("OUT", db), status="pending", **data.model_dump())
    db.add(o); db.flush(); return success_response(o)

@router.get("/outbound-orders")
def list_outbound(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.scalar(select(func.count(OutboundOrder.id))) or 0
    items = list(db.scalars(select(OutboundOrder).offset((page-1)*page_size).limit(page_size)))
    return page_response(items, total, page, page_size)

@router.get("/outbound-orders/{oid}")
def get_outbound(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(db.get(OutboundOrder, oid))

@router.post("/outbound-orders/{oid}/ship")
def ship_route(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(ship_order(db, oid))

@router.post("/outbound-orders/{oid}/sign")
def sign_route(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(sign_order(db, oid))

@router.post("/outbound-orders/{oid}/cancel")
def cancel_route(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(cancel_order(db, oid))
