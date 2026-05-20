from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recent_7_sales: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    recent_30_sales: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    avg_daily_sales: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommended_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommended_supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    shortage_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    days_until_stockout: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    reason_enhanced: Mapped[str | None] = mapped_column(String(1000))
    llm_provider: Mapped[str] = mapped_column(String(30), default="rule", nullable=False)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    adoption_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    store = relationship("Store")
    product = relationship("Product")
    supplier = relationship("Supplier")
