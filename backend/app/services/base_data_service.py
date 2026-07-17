from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db_errors import raise_product_integrity_error
from app.core.exceptions import BusinessException
from app.models.product import Product
from app.models.store import Store
from app.models.warehouse import Warehouse
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.store import StoreCreate, StoreUpdate
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


def create_product(db: Session, payload: ProductCreate) -> Product:
    item = Product(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise_product_integrity_error(exc)
    db.refresh(item)
    return item


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    item = db.get(Product, product_id)
    if not item:
        raise BusinessException("product not found", 404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise_product_integrity_error(exc)
    db.refresh(item)
    return item


def deactivate_product(db: Session, product_id: int) -> None:
    item = db.get(Product, product_id)
    if not item:
        raise BusinessException("product not found", 404)
    item.is_active = False
    db.commit()


def create_warehouse(db: Session, payload: WarehouseCreate) -> Warehouse:
    item = Warehouse(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_warehouse(db: Session, warehouse_id: int, payload: WarehouseUpdate) -> Warehouse:
    item = db.get(Warehouse, warehouse_id)
    if not item:
        raise BusinessException("warehouse not found", 404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def deactivate_warehouse(db: Session, warehouse_id: int) -> None:
    item = db.get(Warehouse, warehouse_id)
    if not item:
        raise BusinessException("warehouse not found", 404)
    item.status = "inactive"
    db.commit()


def create_store(db: Session, payload: StoreCreate) -> Store:
    item = Store(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_store(db: Session, store_id: int, payload: StoreUpdate) -> Store:
    item = db.get(Store, store_id)
    if not item:
        raise BusinessException("store not found", 404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def deactivate_store(db: Session, store_id: int) -> None:
    item = db.get(Store, store_id)
    if not item:
        raise BusinessException("store not found", 404)
    item.business_status = "inactive"
    db.commit()
