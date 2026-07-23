from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from .models import Warehouse

def list_warehouses(db: Session, page=1, page_size=20, keyword=None):
    q = select(Warehouse)
    if keyword: q = q.where(Warehouse.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset((page-1)*page_size).limit(page_size)))
    return items, total

def create_warehouse(db: Session, data: dict):
    w = Warehouse(**data); db.add(w); db.flush(); return w

def get_warehouse(db: Session, wid: int):
    w = db.get(Warehouse, wid)
    if not w: raise BusinessException("warehouse not found", 404)
    return w
