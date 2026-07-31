"""统一数据模型 — 传统的 app/domain 层。

所有业务表在此定义。AI 相关的模型（recommendation_agent、analysis_agent）
仍保留在 agents/ 目录下通过 Sisyphus 加载。
"""

from app.models.user import User
from app.models.product import Product, Category
from app.models.supplier import Supplier, SupplierProduct, SupplierScoreSnapshot
from app.models.procurement import PurchaseOrder, PurchaseOrderItem, InboundOrder, InboundItem
from app.models.inventory import Inventory
from app.models.warehouse import Warehouse
from app.models.store import Store
from app.models.fulfillment import ReplenishmentRequest, OutboundOrder, OutboundItem
from app.models.transaction import StockTransaction

__all__ = [
    "User",
    "Product", "Category",
    "Supplier", "SupplierProduct", "SupplierScoreSnapshot",
    "PurchaseOrder", "PurchaseOrderItem", "InboundOrder", "InboundItem",
    "Inventory",
    "Warehouse",
    "Store",
    "ReplenishmentRequest", "OutboundOrder", "OutboundItem",
    "StockTransaction",
]
