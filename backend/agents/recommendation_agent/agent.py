from fastapi import APIRouter
from kernel.common.base_agent import BaseAgent, AgentInfo

class RecommendationAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(name="recommendation_agent", description="AI补货建议", owns_tables=["ai_recommendations","monthly_sales_facts","promotions"])
    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]
    def register_subscriptions(self) -> dict:
        return {}
    def on_startup(self): pass
    def on_shutdown(self): pass
