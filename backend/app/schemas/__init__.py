"""API 请求/响应模型（Pydantic schema）。

从 app/api/routers/*.py 内嵌的 BaseModel 抽取而来，
按领域分文件管理，router 层统一从此处导入。
"""

from app.schemas.users import LoginRequest, VerificationCodeRequest, RegisterRequest
from app.schemas.products import ProductCreate
from app.schemas.suppliers import SupplierCreate, SupplierProductBind
from app.schemas.procurement import POItem, POCreate, InboundCreate, BatchCompleteInboundRequest
from app.schemas.inventory import AdjustReq
from app.schemas.stores import StoreCreate
from app.schemas.warehouses import WarehouseCreate
from app.schemas.fulfillment import ReplenishCreate, OutboundCreate

__all__ = [
    "LoginRequest", "VerificationCodeRequest", "RegisterRequest",
    "ProductCreate",
    "SupplierCreate", "SupplierProductBind",
    "POItem", "POCreate", "InboundCreate", "BatchCompleteInboundRequest",
    "AdjustReq",
    "StoreCreate",
    "WarehouseCreate",
    "ReplenishCreate", "OutboundCreate",
]
