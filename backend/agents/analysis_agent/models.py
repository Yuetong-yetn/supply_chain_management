"""LLM 分析结果存储模型 — 库存预警分析和补货风险分析的结果。"""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from kernel.common.database import Base


class InventoryWarningAnalysis(Base):
    """库存预警 LLM 分析结果

    每次库存变动后自动触发 LLM 分析，记录分析结论。
    前端展示预警信息时优先使用此表数据，LLM 分析失败时退化为规则预警。
    """
    __tablename__ = "inventory_warning_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    location_type: Mapped[str] = mapped_column(String(20), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))

    # 分析时的快照数据
    current_quantity: Mapped[int] = mapped_column(Integer, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    max_stock: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)

    # LLM 分析结论
    warning_label: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="分析结果：critical_stockout / stockout / overstock / none",
    )
    analysis_text: Mapped[str] = mapped_column(Text, default="", comment="LLM 分析理由")
    llm_provider: Mapped[str] = mapped_column(String(30), default="rule")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # 触发分析的事件信息
    triggered_by_event: Mapped[str] = mapped_column(String(50), default="", comment="触发分析的事件类型")
    inventory_id: Mapped[int | None] = mapped_column(ForeignKey("inventory.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True,
    )


class RestockRiskAnalysis(Base):
    """补货风险 LLM 分析结果

    库存变动后自动重新评估受影响门店/商品的补货风险。
    此表是 ai_recommendations 的补充分析层，不替代补货建议主表。
    """
    __tablename__ = "restock_risk_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)

    # 分析时的快照数据
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    avg_daily_sales: Mapped[float] = mapped_column(Float, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    days_until_stockout: Mapped[float] = mapped_column(Float, default=0)
    recommended_qty: Mapped[int] = mapped_column(Integer, default=0)

    # LLM 分析结论
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="风险等级：high / medium / low",
    )
    analysis_text: Mapped[str] = mapped_column(Text, default="", comment="LLM 分析理由")
    llm_provider: Mapped[str] = mapped_column(String(30), default="rule")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    triggered_by_event: Mapped[str] = mapped_column(String(50), default="")
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("ai_recommendations.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True,
    )
