from typing import Any, Callable
from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class AnalyticsAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="analytics_agent", description="看板与统计", owns_tables=[])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict[str, Callable]:
        return {"inventory.warning.triggered": self.on_warning}
    def on_startup(self): pass
    def on_shutdown(self): pass
    def on_warning(self, event: Any): pass
