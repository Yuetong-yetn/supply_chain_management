from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class MonitoringAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="monitoring_agent", description="系统监控与健康检查", owns_tables=[])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
