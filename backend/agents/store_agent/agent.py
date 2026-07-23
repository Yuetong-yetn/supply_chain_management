from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class StoreAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="store_agent", description="门店管理", owns_tables=["stores"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
