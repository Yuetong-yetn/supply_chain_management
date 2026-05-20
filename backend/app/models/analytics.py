from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MonthlySalesFact(Base):
    __tablename__ = "monthly_sales_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    retail_sales: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    retail_transfers: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    warehouse_sales: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    promo_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SupplierScoreSnapshot(Base):
    __tablename__ = "supplier_score_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_lead_time_days: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_purchase_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    delayed_arrival_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    score_source: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier = relationship("Supplier")


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    promotion_name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    promo_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
