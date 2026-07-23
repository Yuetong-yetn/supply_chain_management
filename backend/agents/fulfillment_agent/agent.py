from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class FulfillmentAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="fulfillment_agent", description="出库与履约管理", owns_tables=["replenishment_requests","outbound_orders","outbound_items"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
