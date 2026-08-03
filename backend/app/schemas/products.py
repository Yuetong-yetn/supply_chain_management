"""商品相关请求模型。"""

from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_code: str; name: str; barcode: str | None = None
    category_id: int | None = None; spec: str | None = None; unit: str | None = None
    shelf_life_days: int | None = None; default_safety_stock: int = 0
