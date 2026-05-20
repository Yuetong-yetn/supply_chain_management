from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.purchase import PurchaseOrder
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderRead
from app.services.purchase_service import cancel_purchase_order, confirm_purchase_order, create_purchase_order
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@router.post("")
def create(payload: PurchaseOrderCreate, db: Session = Depends(get_db_dep)):
    order = create_purchase_order(db, payload)
    db.commit()
    db.refresh(order)
    return success_response(PurchaseOrderRead.model_validate(order).model_dump())


@router.get("")
def list_orders(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(PurchaseOrder)
    if keyword:
        query = query.where(PurchaseOrder.order_no.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [PurchaseOrderRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(PurchaseOrder, order_id)
    if not item:
        raise BusinessException("purchase order not found", 404)
    return success_response(PurchaseOrderRead.model_validate(item).model_dump())


@router.post("/{order_id}/confirm")
def confirm(order_id: int, db: Session = Depends(get_db_dep)):
    item = confirm_purchase_order(db, order_id)
    db.commit()
    return success_response(PurchaseOrderRead.model_validate(item).model_dump())


@router.post("/{order_id}/cancel")
def cancel(order_id: int, db: Session = Depends(get_db_dep)):
    item = cancel_purchase_order(db, order_id)
    db.commit()
    return success_response(PurchaseOrderRead.model_validate(item).model_dump())
