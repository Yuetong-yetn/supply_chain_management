from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class ProcurementAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="procurement_agent", description="采购与入库管理", owns_tables=["purchase_orders","purchase_order_items","inbound_orders","inbound_items"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
