from typing import Any
from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class SupplierAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="supplier_agent", description="供应商管理", owns_tables=["suppliers","supplier_products","supplier_score_snapshots"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict[str, Any]:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
