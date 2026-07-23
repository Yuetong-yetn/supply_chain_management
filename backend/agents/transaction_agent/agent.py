import logging
from datetime import datetime
from typing import Any, Callable
from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo
from kernel.common.database import SessionLocal

logger = logging.getLogger(__name__)


class TransactionAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="transaction_agent", description="库存流水管理", owns_tables=["stock_transactions"])

    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]

    def register_subscriptions(self) -> dict[str, Callable]:
        return {
            "inventory.stock.increased": self.on_stock_changed,
            "inventory.stock.decreased": self.on_stock_changed,
        }

    def on_startup(self):
        pass

    def on_shutdown(self):
        pass

    def on_stock_changed(self, event: Any):
        """库存变动事件处理：创建库存流水记录。"""
        data = event.data if hasattr(event, "data") else {}
        product_id = data.get("product_id")
        change_quantity = data.get("change_quantity", 0)
        if not product_id:
            logger.warning("[TransactionAgent] Missing product_id in event %s", event)
            return

        from .models import StockTransaction

        db = data.get("_db") or SessionLocal()
        owns_session = "_db" not in data
        try:
            tx = StockTransaction(
                transaction_no=f"TX{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                product_id=product_id,
                transaction_type=data.get("transaction_type", "event"),
                source_location_type=data.get("source_location_type"),
                source_warehouse_id=data.get("source_warehouse_id"),
                source_store_id=data.get("source_store_id"),
                target_location_type=data.get("location_type"),
                target_warehouse_id=data.get("warehouse_id"),
                target_store_id=data.get("store_id"),
                change_quantity=change_quantity,
                before_quantity=data.get("before"),
                after_quantity=data.get("after"),
                operated_by=data.get("operator_id"),
                related_doc_type=data.get("related_doc_type"),
                related_doc_id=data.get("related_doc_id"),
                remark=data.get("remark", f"event: {event.type if hasattr(event, 'type') else 'stock_changed'}"),
            )
            db.add(tx)
            if owns_session:
                db.commit()
            logger.info(
                "[TransactionAgent] recorded stock change: product=%s qty=%d",
                product_id, change_quantity,
            )
        except Exception:
            if owns_session:
                db.rollback()
            logger.exception("[TransactionAgent] on_stock_changed failed")
            if not owns_session:
                raise
        finally:
            if owns_session:
                db.close()
