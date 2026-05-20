from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class CategoryBase(BaseModel):
    name: str
    parent_id: int | None = None
    description: str | None = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryRead(CategoryBase, ORMBase):
    id: int
    created_at: datetime


class ProductBase(BaseModel):
    product_code: str
    name: str
    barcode: str | None = None
    category_id: int | None = None
    spec: str | None = None
    unit: str = "piece"
    shelf_life_days: int | None = None
    default_safety_stock: int = 10
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    barcode: str | None = None
    category_id: int | None = None
    spec: str | None = None
    unit: str | None = None
    shelf_life_days: int | None = None
    default_safety_stock: int | None = None
    is_active: bool | None = None


class ProductRead(ProductBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime
