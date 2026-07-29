"""统一 LLM 分析服务 — 库存预警 + 补货风险自动分析。

所有外部 LLM 调用集中在此模块，各 Agent 通过它进行异步分析。
LLM Provider 切换（deepseek / rule）在此模块内部处理。
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from kernel.common.config import get_settings

logger = logging.getLogger(__name__)


# ── 数据结构 ──────────────────────────────────────────────


@dataclass
class LLMAnalysisResult:
    """LLM 分析结果统一返回结构"""
    label: str                  # 分类标签：risk_level / warning_type
    analysis: str               # 大模型分析文本
    llm_provider: str = "rule"  # 实际使用的 provider
    raw_response: str = ""      # 原始响应（调试用）
    confidence: float = 0.0     # 置信度


@dataclass
class InventoryRiskContext:
    """库存预警分析上下文"""
    product_id: int
    product_name: str
    location_type: str
    location_name: str
    current_quantity: int
    safety_stock: int
    max_stock: int
    available_quantity: int
    recent_outbound_7d: float = 0  # 近7日销量
    recent_outbound_30d: float = 0  # 近30日销量


@dataclass
class RestockRiskContext:
    """补货风险分析上下文"""
    store_id: int
    store_name: str
    product_id: int
    product_name: str
    current_stock: int
    avg_daily_sales: float
    safety_stock: int
    lead_time_days: int
    days_until_stockout: float
    recent_30_sales: float
    has_promotion: bool
    recommended_qty: int


@dataclass
class SupplierEvalContext:
    """供应商综合评估上下文"""
    supplier_id: int
    supplier_name: str
    product_count: int
    avg_lead_time_days: float
    avg_on_time_rate: float
    avg_quality_score: float
    delayed_count: int
    total_purchase_amount: float = 0
    cooperation_duration_months: int = 0  # 合作时长（月）


@dataclass
class ReasonEnhanceContext:
    """补货建议理由增强上下文"""
    product_name: str
    store_name: str
    current_stock: int
    avg_daily_sales: float
    safety_stock: int
    recommended_qty: int
    risk_level: str
    days_until_stockout: float
    lead_time_days: int = 0
    has_promotion: bool = False
    recent_30_sales: float = 0
    original_reason: str = ""  # 规则生成的原由文本


# ── Provider 抽象 ─────────────────────────────────────────


class BaseLLMProvider:
    """LLM Provider 基类"""
    name = "rule"

    def analyze_inventory_risk(self, ctx: InventoryRiskContext) -> LLMAnalysisResult:
        raise NotImplementedError

    def evaluate_restock_risk(self, ctx: RestockRiskContext) -> LLMAnalysisResult:
        raise NotImplementedError

    def evaluate_supplier(self, ctx: SupplierEvalContext) -> LLMAnalysisResult:
        raise NotImplementedError

    def enhance_reason(self, ctx: ReasonEnhanceContext) -> LLMAnalysisResult:
        raise NotImplementedError


class RuleProvider(BaseLLMProvider):
    """规则降级 Provider — 使用原硬编码阈值"""
    name = "rule"

    def analyze_inventory_risk(self, ctx: InventoryRiskContext) -> LLMAnalysisResult:
        if ctx.current_quantity <= ctx.safety_stock * 0.5:
            label = "critical_stockout"
            analysis = f"严重缺货：当前库存{ctx.current_quantity}，低于安全库存{ctx.safety_stock}的50%"
        elif ctx.current_quantity <= ctx.safety_stock:
            label = "stockout"
            analysis = f"库存不足：当前库存{ctx.current_quantity}，低于安全库存{ctx.safety_stock}"
        elif ctx.current_quantity >= max(ctx.max_stock, ctx.safety_stock * 4):
            label = "overstock"
            analysis = f"库存积压：当前库存{ctx.current_quantity}，超过最大库存{ctx.max_stock}"
        else:
            label = "none"
            analysis = "库存正常"
        return LLMAnalysisResult(label=label, analysis=analysis, llm_provider="rule")

    def evaluate_restock_risk(self, ctx: RestockRiskContext) -> LLMAnalysisResult:
        if ctx.days_until_stockout <= ctx.lead_time_days:
            label = "high"
        elif ctx.days_until_stockout <= ctx.lead_time_days + 3:
            label = "medium"
        else:
            label = "low"
        analysis = f"当前库存{ctx.current_stock}，预计{ctx.days_until_stockout:.1f}天后缺货，风险等级：{label}"
        return LLMAnalysisResult(label=label, analysis=analysis, llm_provider="rule")

    def evaluate_supplier(self, ctx: SupplierEvalContext) -> LLMAnalysisResult:
        """规则型供应商评分（与原 handler 一致）"""
        if ctx.product_count == 0:
            return LLMAnalysisResult(label="0", analysis="无供货商品", llm_provider="rule")
        delayed = max(0, int(ctx.product_count * (1 - ctx.avg_on_time_rate) * 10))
        score = max(0, min(100, round(
            100 - ctx.avg_lead_time_days * 2 - delayed * 5
                + ctx.avg_on_time_rate * 20 + ctx.avg_quality_score * 10, 2
        )))
        score_str = str(score)
        analysis = (
            f"综合评分{score}分。评分依据：平均交货周期{ctx.avg_lead_time_days:.1f}天"
            f"（扣{ctx.avg_lead_time_days*2:.0f}分），"
            f"准时到货率{ctx.avg_on_time_rate:.0%}（加{ctx.avg_on_time_rate*20:.0f}分），"
            f"质量评分{ctx.avg_quality_score:.1f}（加{ctx.avg_quality_score/10:.0f}分），"
            f"估算延迟{ctx.delayed_count}次（扣{delayed*5}分）"
        )
        return LLMAnalysisResult(label=score_str, analysis=analysis, llm_provider="rule")

    def enhance_reason(self, ctx: ReasonEnhanceContext) -> LLMAnalysisResult:
        """规则型理由增强 — 使用原有格式化文本"""
        analysis = (
            f"{ctx.store_name}的{ctx.product_name}当前库存{ctx.current_stock}件，"
            f"日均销量{ctx.avg_daily_sales:.1f}件/天，"
            f"安全库存{ctx.safety_stock}件，"
            f"预计{ctx.days_until_stockout:.1f}天后缺货。"
        )
        if ctx.risk_level == "high":
            analysis += f"建议立即补货{ctx.recommended_qty}件以避免断货。"
        elif ctx.risk_level == "medium":
            analysis += f"建议近期安排补货{ctx.recommended_qty}件。"
        else:
            analysis += f"目前库存充足，建议维持当前库存水平。"
        if ctx.has_promotion:
            analysis += "该商品正在进行促销活动，建议适当增加补货量。"
        return LLMAnalysisResult(label=ctx.risk_level, analysis=analysis, llm_provider="rule")


class DeepseekProvider(BaseLLMProvider):
    """DeepSeek API Provider — 复用 httpx.Client 连接池提升并发性能。"""
    name = "deepseek"

    def __init__(self, api_key: str, base_url: str, model: str,
                 timeout: int = 30, max_retries: int = 2):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = float(timeout)
        self.max_retries = max(0, max_retries)
        # 复用连接池：避免每个请求新建 TCP 连接，提升并发性能
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    def _call(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        """调用 DeepSeek Chat API（含重试），返回解析后的 JSON dict 或 None"""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.post(
                    "/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 512,
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                content = body["choices"][0]["message"]["content"]
                # 尝试提取 JSON（可能被 Markdown 代码块包裹）
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    content = content.rsplit("```", 1)[0]
                return json.loads(content.strip())
            except httpx.TimeoutException:
                last_error = f"request timed out (attempt {attempt + 1})"
                logger.warning("[DeepSeek] %s", last_error)
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                logger.warning("[DeepSeek] %s", last_error)
                # 4xx 错误不重试
                if 400 <= e.response.status_code < 500:
                    break
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                last_error = f"parse error (attempt {attempt + 1}): {e}"
                logger.warning("[DeepSeek] %s", last_error)
            except Exception as e:
                last_error = f"unexpected error (attempt {attempt + 1}): {e}"
                logger.warning("[DeepSeek] %s", last_error)
            if attempt < self.max_retries:
                wait = 0.5 * (2 ** attempt)
                time.sleep(wait)
        logger.error("[DeepSeek] All %d attempts failed: %s", self.max_retries + 1, last_error)
        return None

    def analyze_inventory_risk(self, ctx: InventoryRiskContext) -> LLMAnalysisResult:
        system_prompt = (
            "你是一位供应链库存管理专家。根据库存数据判断是否触发预警。"
            "请严格按照 JSON 格式回复：{\"label\": \"critical_stockout|stockout|overstock|none\", \"analysis\": \"理由\"}"
        )
        user_prompt = (
            f"请分析以下库存数据：\n"
            f"- 商品：{ctx.product_name}\n"
            f"- 位置：{ctx.location_name}（{ctx.location_type}）\n"
            f"- 当前库存：{ctx.current_quantity}\n"
            f"- 安全库存：{ctx.safety_stock}\n"
            f"- 最大库存：{ctx.max_stock}\n"
            f"- 可用库存：{ctx.available_quantity}\n"
            f"- 近7日销量：{ctx.recent_outbound_7d:.0f}\n"
            f"- 近30日销量：{ctx.recent_outbound_30d:.0f}\n\n"
            f"请判断是否需要预警："
            f"critical_stockout（≤安全库存50%）、"
            f"stockout（≤安全库存）、"
            f"overstock（≥最大库存或安全库存4倍）、"
            f"none（正常）"
        )
        result = self._call(system_prompt, user_prompt)
        if result and isinstance(result, dict):
            return LLMAnalysisResult(
                label=result.get("label", "none"),
                analysis=result.get("analysis", ""),
                llm_provider="deepseek",
                raw_response=json.dumps(result, ensure_ascii=False),
                confidence=result.get("confidence", 0.0),
            )
        # 降级到规则
        logger.info("[DeepSeek] Fallback to rule for inventory risk analysis")
        return RuleProvider().analyze_inventory_risk(ctx)

    def evaluate_restock_risk(self, ctx: RestockRiskContext) -> LLMAnalysisResult:
        system_prompt = (
            "你是一位零售供应链分析师。根据商品销售、库存和补货数据评估缺货风险等级。"
            "请严格按照 JSON 格式回复：{\"label\": \"high|medium|low\", \"analysis\": \"分析理由\", \"confidence\": 0.0~1.0}"
        )
        user_prompt = (
            f"请评估以下门店商品的补货风险：\n"
            f"- 门店：{ctx.store_name}\n"
            f"- 商品：{ctx.product_name}\n"
            f"- 当前库存：{ctx.current_stock} 件\n"
            f"- 日均销量：{ctx.avg_daily_sales:.1f} 件/天\n"
            f"- 安全库存：{ctx.safety_stock} 件\n"
            f"- 供应商提前期：{ctx.lead_time_days} 天\n"
            f"- 预计缺货天数：{ctx.days_until_stockout:.1f} 天\n"
            f"- 近30天销量：{ctx.recent_30_sales:.0f} 件\n"
            f"- 建议补货量：{ctx.recommended_qty} 件\n"
            f"- 是否有促销活动：{'是' if ctx.has_promotion else '否'}\n\n"
            f"请判断风险等级：high（即将断货）、medium（需关注）、low（充足）。"
            f"注意供应商提前期{ctx.lead_time_days}天是关键参考因素。"
        )
        result = self._call(system_prompt, user_prompt)
        if result and isinstance(result, dict):
            return LLMAnalysisResult(
                label=result.get("label", "low"),
                analysis=result.get("analysis", ""),
                llm_provider="deepseek",
                raw_response=json.dumps(result, ensure_ascii=False),
                confidence=result.get("confidence", 0.0),
            )
        # 降级到规则
        logger.info("[DeepSeek] Fallback to rule for restock risk analysis")
        return RuleProvider().evaluate_restock_risk(ctx)

    def evaluate_supplier(self, ctx: SupplierEvalContext) -> LLMAnalysisResult:
        system_prompt = (
            "你是一位供应链质量管理专家。根据供应商的履约数据综合评分。"
            "请参考以下评分维度：\n"
            "1. 交货周期（满分30分）：周期越短越好\n"
            "2. 到货准时率（满分30分）：越接近100%越好\n"
            "3. 质量评分（满分30分）：越高越好\n"
            "4. 延迟记录（减分项）：延迟次数越多扣分越多\n"
            "5. 合作时长（加分项）：长期稳定合作为加分\n\n"
            "请严格按照 JSON 格式回复："
            "{\"label\": \"0-100的整数评分\", \"analysis\": \"评分分析理由\", \"confidence\": 0.0~1.0}"
        )
        user_prompt = (
            f"请评估以下供应商的综合表现：\n"
            f"- 供应商名称：{ctx.supplier_name}\n"
            f"- 供货商品数量：{ctx.product_count}\n"
            f"- 平均交货周期：{ctx.avg_lead_time_days:.1f} 天\n"
            f"- 平均准时到货率：{ctx.avg_on_time_rate:.2f}（1.0=100%）\n"
            f"- 平均质量评分：{ctx.avg_quality_score:.1f}（满分100）\n"
            f"- 估算延迟到货次数：{ctx.delayed_count} 次\n"
            f"- 合作时长：{ctx.cooperation_duration_months} 个月\n"
            f"- 采购总金额：{ctx.total_purchase_amount:.2f}\n\n"
            f"请基于你的行业经验给出综合评分（0-100分），"
            f"并详细说明评分依据和业务建议。"
        )
        result = self._call(system_prompt, user_prompt)
        if result and isinstance(result, dict):
            label = result.get("label", "0")
            # 尝试提取数值评分
            try:
                score = float(label)
                label = str(max(0, min(100, round(score))))
            except (ValueError, TypeError):
                label = "0"
            return LLMAnalysisResult(
                label=label,
                analysis=result.get("analysis", ""),
                llm_provider="deepseek",
                raw_response=json.dumps(result, ensure_ascii=False),
                confidence=result.get("confidence", 0.0),
            )
        logger.info("[DeepSeek] Fallback to rule for supplier evaluation")
        return RuleProvider().evaluate_supplier(ctx)

    def enhance_reason(self, ctx: ReasonEnhanceContext) -> LLMAnalysisResult:
        system_prompt = (
            "你是一位经验丰富的零售门店经理。请根据库存和销售数据，"
            "用自然、专业的语气生成一段补货建议理由。"
            "要求：语言流畅、有分析逻辑、给出具体行动建议。"
            "请严格按照 JSON 格式回复："
            "{\"analysis\": \"建议理由文本(50-150字)\", \"confidence\": 0.0~1.0}"
        )
        risk_desc = {"high": "即将断货", "medium": "需关注", "low": "库存充足"}
        user_prompt = (
            f"请为以下商品生成一段补货建议理由：\n"
            f"- 门店：{ctx.store_name}\n"
            f"- 商品：{ctx.product_name}\n"
            f"- 当前库存：{ctx.current_stock} 件\n"
            f"- 日均销量：{ctx.avg_daily_sales:.1f} 件/天\n"
            f"- 安全库存：{ctx.safety_stock} 件\n"
            f"- 建议补货量：{ctx.recommended_qty} 件\n"
            f"- 风险等级：{ctx.risk_level}（{risk_desc.get(ctx.risk_level, '')}）\n"
            f"- 预计缺货天数：{ctx.days_until_stockout:.1f} 天\n"
            f"- 供应商提前期：{ctx.lead_time_days} 天\n"
            f"- 是否有促销活动：{'是' if ctx.has_promotion else '否'}\n"
            f"- 近30天销量：{ctx.recent_30_sales:.0f} 件\n\n"
            f"请结合以上数据给出具体的、有指导意义的补货建议。"
        )
        result = self._call(system_prompt, user_prompt)
        if result and isinstance(result, dict):
            analysis = result.get("analysis", "")
            return LLMAnalysisResult(
                label=ctx.risk_level,
                analysis=analysis,
                llm_provider="deepseek",
                raw_response=json.dumps(result, ensure_ascii=False),
                confidence=result.get("confidence", 0.0),
            )
        logger.info("[DeepSeek] Fallback to rule for reason enhancement")
        return RuleProvider().enhance_reason(ctx)


# ── 工厂 ──────────────────────────────────────────────────


def create_llm_provider() -> BaseLLMProvider:
    """根据配置创建 LLM Provider。默认使用 DeepSeek，失败时降级到规则。"""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "deepseek":
        api_key = settings.deepseek_api_key_value
        if api_key:
            return DeepseekProvider(
                api_key=api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                timeout=settings.llm_timeout_seconds,
                max_retries=settings.llm_max_retries,
            )
        logger.warning("[LLM] DeepSeek configured but no API key found. "
                       "Set DEEPSEEK_API_KEY or DEEPSEEK_API_KEY_FILE in .env. "
                       "Falling back to rule-based analysis.")
    else:
        logger.warning("[LLM] Unknown provider '%s', falling back to rule.", provider)
    return RuleProvider()


# ── 全局单例 ──────────────────────────────────────────────

_llm_provider: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider()
    return _llm_provider


def clear_provider_cache():
    """清空 Provider 缓存（测试用）"""
    global _llm_provider
    _llm_provider = None
