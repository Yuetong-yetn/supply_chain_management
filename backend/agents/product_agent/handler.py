from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from .models import Product, Category

def list_products(db: Session, page: int = 1, page_size: int = 20, keyword: str = None):
    q = select(Product)
    if keyword:
        q = q.where(Product.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset((page-1)*page_size).limit(page_size)))
    return items, total

def create_product(db: Session, data: dict):
    obj = Product(**data)
    db.add(obj)
    db.flush()
    return obj

def get_product(db: Session, pid: int):
    p = db.get(Product, pid)
    if not p: raise BusinessException("product not found", 404)
    return p

def update_product(db: Session, pid: int, data: dict):
    p = get_product(db, pid)
    for k, v in data.items():
        if hasattr(p, k): setattr(p, k, v)
    db.flush()
    return p

def delete_product(db: Session, pid: int):
    p = get_product(db, pid)
    p.is_active = False
    db.flush()
    return p

def list_categories(db: Session):
    return list(db.scalars(select(Category)))

def create_category(db: Session, data: dict):
    obj = Category(**data)
    db.add(obj)
    db.flush()
    return obj
