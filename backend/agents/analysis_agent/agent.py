"""LLM Analysis Agent — 自动后台分析 Agent。

订阅库存变动事件，自动触发 LLM 进行库存预警分析和补货风险分析。
分析结果写入专用表，供前端和 dashboard 查询。
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from fastapi import APIRouter

from kernel.common.base_agent import BaseAgent, AgentInfo

logger = logging.getLogger(__name__)

# 后台分析线程池（非 daemon，优雅关闭时等待任务完成）
_analysis_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llm-analysis")


class AnalysisAgent(BaseAgent):
    """LLM 自动分析 Agent — 事件驱动，不阻塞业务主流程。"""

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            name="analysis_agent",
            description="LLM自动分析（库存预警+补货风险）",
            owns_tables=["inventory_warning_analyses", "restock_risk_analyses"],
        )

    def register_routes(self) -> list[APIRouter]:
        from .router import router
        return [router]

    def register_subscriptions(self) -> dict[str, Callable]:
        """订阅库存变动事件，自动触发 LLM 分析"""
        return {
            "inventory.stock.increased": self._on_stock_changed,
            "inventory.stock.decreased": self._on_stock_changed,
        }

    def on_startup(self):
        logger.info("[AnalysisAgent] Started. Listening for stock change events.")

    def on_shutdown(self):
        logger.info("[AnalysisAgent] Shutting down, waiting for background analysis tasks...")
        _analysis_executor.shutdown(wait=True, cancel_futures=False)
        logger.info("[AnalysisAgent] Shutdown complete.")

    def _on_stock_changed(self, event: Any) -> None:
        """库存变动事件回调 — 在后台线程池中运行 LLM 分析"""
        data = event.data if hasattr(event, "data") else {}
        data["_event_type"] = event.type if hasattr(event, "type") else "inventory.stock.changed"

        _analysis_executor.submit(self._run_analysis, data)
        logger.debug(
            "[AnalysisAgent] Submitted background analysis task for product=%s",
            data.get("product_id"),
        )

    @staticmethod
    def _run_analysis(data: dict[str, Any]) -> None:
        """在线程池中运行 LLM 分析"""
        from .handler import on_stock_changed
        try:
            on_stock_changed(data)
        except Exception:
            logger.exception("[AnalysisAgent] Background analysis error")
