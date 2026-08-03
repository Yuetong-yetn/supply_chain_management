from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from app.core.database import get_db, Session
from app.core.response import success_response, page_response
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.procurement import POItem, POCreate, InboundCreate, BatchCompleteInboundRequest
from app.services.procurement_service import create_purchase_order, confirm_purchase_order, cancel_purchase_order, generate_no, complete_inbound, batch_complete_inbound
from app.models.procurement import PurchaseOrder, InboundOrder

router = APIRouter(prefix="/api", tags=["procurement"])


@router.post("/purchase-orders")
def create_po(data: POCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_purchase_order(db, data.model_dump()))


@router.get("/purchase-orders")
def list_po(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.scalar(select(func.count(PurchaseOrder.id))) or 0
    items = list(db.scalars(select(PurchaseOrder).offset((page - 1) * page_size).limit(page_size)))
    return page_response(items, total, page, page_size)


@router.get("/purchase-orders/{oid}")
def get_po(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(db.get(PurchaseOrder, oid))


@router.post("/purchase-orders/{oid}/confirm")
def confirm_po(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(confirm_purchase_order(db, oid))


@router.post("/purchase-orders/{oid}/cancel")
def cancel_po(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(cancel_purchase_order(db, oid))


@router.post("/inbound-orders")
def create_inbound(data: InboundCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    i = InboundOrder(inbound_no=generate_no("IN", db), **data.model_dump())
    db.add(i)
    db.flush()
    return success_response(i)


@router.get("/inbound-orders")
def list_inbound(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.scalar(select(func.count(InboundOrder.id))) or 0
    items = list(db.scalars(select(InboundOrder).offset((page - 1) * page_size).limit(page_size)))
    return page_response(items, total, page, page_size)


@router.get("/inbound-orders/{iid}")
def get_inbound(iid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(db.get(InboundOrder, iid))


@router.post("/inbound-orders/{iid}/complete")
def complete_inbound_route(iid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(complete_inbound(db, iid))


@router.post("/inbound-orders/batch-complete")
def batch_complete_inbound_route(data: BatchCompleteInboundRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response({"completed": len(batch_complete_inbound(db, data.ids))})
