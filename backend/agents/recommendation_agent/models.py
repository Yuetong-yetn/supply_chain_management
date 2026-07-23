from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from kernel.common.database import Base

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    recent_7_sales: Mapped[float] = mapped_column(Float, default=0)
    recent_30_sales: Mapped[float] = mapped_column(Float, default=0)
    avg_daily_sales: Mapped[float] = mapped_column(Float, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    recommended_quantity: Mapped[int] = mapped_column(Integer, default=0)
    recommended_supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    shortage_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    days_until_stockout: Mapped[float] = mapped_column(Float, default=0)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    reason_enhanced: Mapped[str | None] = mapped_column(String(1000))
    llm_provider: Mapped[str] = mapped_column(String(30), default="rule")
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    adoption_status: Mapped[str] = mapped_column(String(20), default="pending")

class MonthlySalesFact(Base):
    __tablename__ = "monthly_sales_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    retail_sales: Mapped[float] = mapped_column(Float, default=0)
    retail_transfers: Mapped[float] = mapped_column(Float, default=0)
    warehouse_sales: Mapped[float] = mapped_column(Float, default=0)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    promo_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)

class Promotion(Base):
    __tablename__ = "promotions"
    id: Mapped[int] = mapped_column(primary_key=True)
    promotion_name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    promo_factor: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[str | None] = mapped_column(String(255))
