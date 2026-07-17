from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.inbound import InboundOrder
from app.schemas.inbound import InboundOrderCreate, InboundOrderRead
from app.services.inbound_service import complete_inbound_order as complete_inbound_order_service
from app.services.inbound_service import create_from_purchase, create_inbound_order as create_inbound_order_service
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/inbound-orders", tags=["inbound-orders"])


@router.post("")
def create_inbound_order(payload: InboundOrderCreate, db: Session = Depends(get_db_dep)):
    order = create_inbound_order_service(db, payload)
    db.commit()
    db.refresh(order)
    return success_response(InboundOrderRead.model_validate(order).model_dump())


@router.post("/from-purchase/{purchase_order_id}")
def create_inbound_order_from_purchase(purchase_order_id: int, handled_by: int, warehouse_id: int, db: Session = Depends(get_db_dep)):
    order = create_from_purchase(db, purchase_order_id, handled_by, warehouse_id)
    db.commit()
    db.refresh(order)
    return success_response(InboundOrderRead.model_validate(order).model_dump())


@router.post("/{order_id}/complete")
def complete_inbound_order(order_id: int, db: Session = Depends(get_db_dep)):
    try:
        order = complete_inbound_order_service(db, order_id)
        db.commit()
        db.refresh(order)
        return success_response(InboundOrderRead.model_validate(order).model_dump())
    except Exception:
        db.rollback()
        raise


@router.get("")
def list_orders(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(InboundOrder)
    if keyword:
        query = query.where(InboundOrder.inbound_no.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [InboundOrderRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(InboundOrder, order_id)
    if not item:
        raise BusinessException("inbound order not found", 404)
    return success_response(InboundOrderRead.model_validate(item).model_dump())
