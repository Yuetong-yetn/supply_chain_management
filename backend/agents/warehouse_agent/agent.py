from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class WarehouseAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="warehouse_agent", description="仓库管理", owns_tables=["warehouses"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
