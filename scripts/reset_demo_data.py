"""重置演示数据 — 删除所有业务表中的数据。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BE_DIR = ROOT / "backend"
for p in (str(ROOT), str(BE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import text

from kernel.common.database import SessionLocal, is_sqlite_bind
from app.models.user import User
from app.models.product import Product, Category
from app.models.supplier import Supplier, SupplierProduct, SupplierScoreSnapshot
from app.models.warehouse import Warehouse
from app.models.store import Store
from app.models.inventory import Inventory
from app.models.procurement import PurchaseOrder, PurchaseOrderItem, InboundOrder, InboundItem
from app.models.fulfillment import ReplenishmentRequest, OutboundOrder, OutboundItem
from app.models.transaction import StockTransaction
from agents.recommendation_agent.models import AIRecommendation, MonthlySalesFact, Promotion


def _disable_fk(db, disabled: bool):
    """SQLite 下临时关闭外键约束以加速批量删除。"""
    if is_sqlite_bind(db):
        pragma = "OFF" if disabled else "ON"
        db.execute(text(f"PRAGMA foreign_keys = {pragma}"))


if __name__ == "__main__":
    session = SessionLocal()
    try:
        _disable_fk(session, disabled=True)
        try:
            # 按外键依赖顺序从叶子节点到根节点删除
            delete_order = [
                AIRecommendation,
                MonthlySalesFact,
                Promotion,
                SupplierScoreSnapshot,
                StockTransaction,
                ReplenishmentRequest,
                OutboundItem,
                OutboundOrder,
                InboundItem,
                InboundOrder,
                PurchaseOrderItem,
                PurchaseOrder,
                Inventory,
                SupplierProduct,
                Product,
                Category,
                Supplier,
                Store,
                Warehouse,
            ]
            for model in delete_order:
                session.query(model).delete()
        finally:
            _disable_fk(session, disabled=False)
        session.commit()
        print("全部演示数据已删除。")
    except Exception as exc:
        session.rollback()
        print(f"删除失败: {exc}")
    finally:
        session.close()
