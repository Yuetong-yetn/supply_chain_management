from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.replenishment import ReplenishmentRequest
from app.schemas.replenishment import ReplenishmentRequestCreate, ReplenishmentRequestRead
from app.services.replenishment_service import approve_request, convert_to_outbound, create_replenishment_request, reject_request
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/replenishment-requests", tags=["replenishment-requests"])


@router.post("")
def create(payload: ReplenishmentRequestCreate, db: Session = Depends(get_db_dep)):
    item = create_replenishment_request(db, payload)
    db.commit()
    db.refresh(item)
    return success_response(ReplenishmentRequestRead.model_validate(item).model_dump())


@router.get("")
def list_items(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(ReplenishmentRequest)
    if keyword:
        query = query.where(ReplenishmentRequest.request_no.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [ReplenishmentRequestRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.get("/{request_id}")
def get_item(request_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(ReplenishmentRequest, request_id)
    if not item:
        raise BusinessException("request not found", 404)
    return success_response(ReplenishmentRequestRead.model_validate(item).model_dump())


@router.post("/{request_id}/approve")
def approve(request_id: int, audited_by: int, db: Session = Depends(get_db_dep)):
    item = approve_request(db, request_id, audited_by)
    db.commit()
    return success_response(ReplenishmentRequestRead.model_validate(item).model_dump())


@router.post("/{request_id}/reject")
def reject(request_id: int, audited_by: int, db: Session = Depends(get_db_dep)):
    item = reject_request(db, request_id, audited_by)
    db.commit()
    return success_response(ReplenishmentRequestRead.model_validate(item).model_dump())


@router.post("/{request_id}/convert-to-outbound")
def convert(request_id: int, source_warehouse_id: int, handled_by: int, db: Session = Depends(get_db_dep)):
    try:
        item = convert_to_outbound(db, request_id, source_warehouse_id, handled_by)
        db.commit()
        return success_response({"outbound_order_id": item.id, "outbound_no": item.outbound_no})
    except Exception:
        db.rollback()
        raise
