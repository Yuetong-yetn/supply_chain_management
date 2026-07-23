from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from .models import Store

def list_stores(db: Session, page=1, page_size=20, keyword=None):
    q = select(Store)
    if keyword: q = q.where(Store.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset((page-1)*page_size).limit(page_size)))
    return items, total

def create_store(db: Session, data: dict):
    s = Store(**data); db.add(s); db.flush(); return s

def get_store(db: Session, sid: int):
    s = db.get(Store, sid)
    if not s: raise BusinessException("store not found", 404)
    return s
