from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class ProductAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="product_agent", description="商品与品类管理", owns_tables=["products","categories"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
