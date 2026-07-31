"""AI Agent 注册入口 — 只注册 AI 能力层 Agent。

业务逻辑（用户、商品、采购、库存、出库、门店、仓库等）已迁移到 app/ 目录
以传统 MVC 方式组织，不再通过 Sisyphus 注册。

AI Agent 保留在 agents/ 目录下，通过 Sisyphus 注册以维持事件驱动订阅能力。
"""

from kernel.sisyphus.orchestrator import SisyphusOrchestrator


def register_ai_agents(orchestrator: SisyphusOrchestrator) -> None:
    """只注册 AI 能力层 Agent（LLM 分析、补货建议等）。"""
    from agents.recommendation_agent.agent import RecommendationAgent
    from agents.analysis_agent.agent import AnalysisAgent

    for agent in [RecommendationAgent(), AnalysisAgent()]:
        orchestrator.register_agent(agent)
