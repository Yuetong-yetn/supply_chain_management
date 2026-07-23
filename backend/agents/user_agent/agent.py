from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo


class UserAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="user_agent", description="用户与权限管理", owns_tables=["users"])

    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]

    def register_subscriptions(self) -> dict:
        from .events import SUBSCRIPTIONS
        return SUBSCRIPTIONS

    def on_startup(self):
        pass

    def on_shutdown(self):
        pass
