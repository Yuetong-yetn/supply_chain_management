import logging
from typing import Any, Callable
from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo
from kernel.common.database import SessionLocal

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="inventory_agent", description="库存管理", owns_tables=["inventory"])

    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]

    def register_subscriptions(self) -> dict[str, Callable]:
        return {
            "procurement.inbound.completed": self.on_inbound_completed,
            "fulfillment.outbound.shipped": self.on_outbound_shipped,
            "fulfillment.outbound.signed": self.on_store_signed,
        }

    def on_startup(self):
        pass

    def on_shutdown(self):
        pass

    def on_inbound_completed(self, event: Any):
        self._handle("increase", event)

    def on_outbound_shipped(self, event: Any):
        self._handle("decrease", event)

    def on_store_signed(self, event: Any):
        self._handle("increase_store", event)

    def _handle(self, action: str, event: Any):
        """根据事件数据调用 handler 中的库存操作方法。"""
        data = event.data if hasattr(event, "data") else {}
        items = data.get("items", [])
        if not items:
            logger.warning("[InventoryAgent] No items in event %s", event.type if hasattr(event, "type") else "?")
            return

        from .handler import increase_stock, decrease_stock

        db = data.get("_db") or SessionLocal()
        owns_session = "_db" not in data
        try:
            if action == "increase":
                for item in items:
                    warehouse_id = data.get("warehouse_id")
                    increase_stock(
                        db=db,
                        product_id=item.get("product_id"),
                        location_type="warehouse",
                        quantity=item.get("quantity", 0),
                        warehouse_id=warehouse_id,
                        operator_id=data.get("handled_by"),
                        transaction_type="purchase_inbound",
                        related_doc_type="inbound_order",
                        related_doc_id=data.get("inbound_order_id"),
                    )
                logger.info(
                    "[InventoryAgent] inbound completed: processed %d items for warehouse %s",
                    len(items), data.get("warehouse_id"),
                )
            elif action == "decrease":
                for item in items:
                    decrease_stock(
                        db=db,
                        product_id=item.get("product_id"),
                        location_type="warehouse",
                        quantity=item.get("quantity", 0),
                        warehouse_id=data.get("warehouse_id"),
                        operator_id=data.get("handled_by"),
                        transaction_type="outbound_ship",
                        related_doc_type="outbound_order",
                        related_doc_id=data.get("order_id"),
                    )
                logger.info(
                    "[InventoryAgent] outbound shipped: processed %d items from warehouse %s",
                    len(items), data.get("warehouse_id"),
                )
            elif action == "increase_store":
                for item in items:
                    increase_stock(
                        db=db,
                        product_id=item.get("product_id"),
                        location_type="store",
                        quantity=item.get("quantity", 0),
                        store_id=data.get("store_id"),
                        operator_id=data.get("handled_by"),
                        transaction_type="store_sign",
                        related_doc_type="outbound_order",
                        related_doc_id=data.get("order_id"),
                    )
                logger.info(
                    "[InventoryAgent] store signed: processed %d items for store %s",
                    len(items), data.get("store_id"),
                )
            if owns_session:
                db.commit()
        except Exception:
            if owns_session:
                db.rollback()
            logger.exception("[InventoryAgent] _handle(%s) failed", action)
            if not owns_session:
                raise
        finally:
            if owns_session:
                db.close()
