"""LLM 服务 — 转发 kernel.common.llm_service。"""

from kernel.common.llm_service import (
    get_llm_provider,
    ReasonEnhanceContext, RestockRiskContext, SupplierEvalContext,
    InventoryRiskContext, LLMAnalysisResult,
)

__all__ = [
    "get_llm_provider",
    "ReasonEnhanceContext", "RestockRiskContext", "SupplierEvalContext",
    "InventoryRiskContext", "LLMAnalysisResult",
]
