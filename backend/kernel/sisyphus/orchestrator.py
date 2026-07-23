"""Sisyphus Orchestrator — Agent 注册、路由挂载、工作流编排"""

import logging
from fastapi import APIRouter, FastAPI
from kernel.common.base_agent import BaseAgent
from kernel.common.event import event_bus
from kernel.common.response import success_response
from kernel.sisyphus.workflow import WorkflowEngine

logger = logging.getLogger(__name__)


class SisyphusOrchestrator:
    """Sisyphus 总指挥 — 系统的"大脑"。

    职责：
    1. 启动时收集所有 Agent 的注册信息
    2. 对外暴露统一 API 入口，挂载每个 Agent 的路由
    3. 对跨 Agent 请求，编排工作流协调多个 Agent 协作
    4. 提供 Agent 健康检查和元信息查询
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._workflow_engine = WorkflowEngine()
        self.router = APIRouter()
        self.admin_router = APIRouter(prefix="/api/system", tags=["system"])
        self.admin_router.add_api_route("/agents", self.list_agents, methods=["GET"])

    def register_agent(self, agent: BaseAgent) -> None:
        """注册一个 Agent 到系统中"""
        info = agent.info
        if info.name in self._agents:
            raise ValueError(f"Agent '{info.name}' already registered")
        self._agents[info.name] = agent
        for route in agent.register_routes():
            self.router.include_router(route)
        for event_type, handler in agent.register_subscriptions().items():
            event_bus.subscribe(event_type, handler)
        logger.info("[Sisyphus] Registered agent: %s (%s)", info.name, info.description)

    def mount_to_app(self, app: FastAPI) -> None:
        """挂载所有路由到 FastAPI 应用"""
        app.include_router(self.router)
        app.include_router(self.admin_router)

    def list_agents(self):
        return success_response(
            {
                "agents": [
                    {
                        "name": agent.info.name,
                        "description": agent.info.description,
                        "version": agent.info.version,
                        "owns_tables": agent.info.owns_tables,
                    }
                    for agent in self._agents.values()
                ]
            }
        )

    @property
    def agents(self) -> dict[str, BaseAgent]:
        return dict(self._agents)

    def get_agent(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)
