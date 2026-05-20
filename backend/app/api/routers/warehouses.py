from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])


@router.get("")
def list_warehouses(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(Warehouse)
    if keyword:
        query = query.where(Warehouse.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [WarehouseRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.post("")
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db_dep)):
    item = Warehouse(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(WarehouseRead.model_validate(item).model_dump())


@router.get("/{warehouse_id}")
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(Warehouse, warehouse_id)
    if not item:
        raise BusinessException("warehouse not found", 404)
    return success_response(WarehouseRead.model_validate(item).model_dump())


@router.put("/{warehouse_id}")
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate, db: Session = Depends(get_db_dep)):
    item = db.get(Warehouse, warehouse_id)
    if not item:
        raise BusinessException("warehouse not found", 404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return success_response(WarehouseRead.model_validate(item).model_dump())


@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(Warehouse, warehouse_id)
    if not item:
        raise BusinessException("warehouse not found", 404)
    item.status = "inactive"
    db.commit()
    return success_response(message="deleted")
