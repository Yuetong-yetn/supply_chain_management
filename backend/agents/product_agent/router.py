from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import list_products, get_product, create_product, update_product, delete_product, list_categories, create_category

router = APIRouter(prefix="/api", tags=["products"])

class ProductCreate(BaseModel):
    product_code: str; name: str; barcode: str | None = None
    category_id: int | None = None; spec: str | None = None; unit: str | None = None
    shelf_life_days: int | None = None; default_safety_stock: int = 0

@router.get("/products")
def get_products(page: int = Query(1), page_size: int = Query(20), keyword: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total = list_products(db, page, page_size, keyword)
    return page_response(items, total, page, page_size)

@router.post("/products")
def create_product_route(data: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_product(db, data.model_dump()))

@router.get("/products/{pid}")
def get_product_route(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_product(db, pid))

@router.put("/products/{pid}")
def update_product_route(pid: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(update_product(db, pid, data))

@router.delete("/products/{pid}")
def delete_product_route(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(delete_product(db, pid), message="deleted")

@router.get("/categories")
def get_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(list_categories(db))

@router.post("/categories")
def create_category_route(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_category(db, data))
