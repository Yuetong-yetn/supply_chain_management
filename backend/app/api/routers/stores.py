from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreRead, StoreUpdate
from app.services.base_data_service import create_store as create_store_service
from app.services.base_data_service import deactivate_store, update_store as update_store_service
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("")
def list_stores(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(Store)
    if keyword:
        query = query.where(Store.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [StoreRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.post("")
def create_store(payload: StoreCreate, db: Session = Depends(get_db_dep)):
    item = create_store_service(db, payload)
    return success_response(StoreRead.model_validate(item).model_dump())


@router.get("/{store_id}")
def get_store(store_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(Store, store_id)
    if not item:
        raise BusinessException("store not found", 404)
    return success_response(StoreRead.model_validate(item).model_dump())


@router.put("/{store_id}")
def update_store(store_id: int, payload: StoreUpdate, db: Session = Depends(get_db_dep)):
    item = update_store_service(db, store_id, payload)
    return success_response(StoreRead.model_validate(item).model_dump())


@router.delete("/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db_dep)):
    deactivate_store(db, store_id)
    return success_response(message="deleted")
