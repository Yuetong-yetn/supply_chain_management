from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_location_type: Mapped[str | None] = mapped_column(String(20))
    source_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    source_store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    target_location_type: Mapped[str | None] = mapped_column(String(20))
    target_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    target_store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    change_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    before_quantity: Mapped[int | None] = mapped_column(Integer)
    after_quantity: Mapped[int | None] = mapped_column(Integer)
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    operated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    related_doc_type: Mapped[str | None] = mapped_column(String(50))
    related_doc_id: Mapped[int | None] = mapped_column(Integer)
    remark: Mapped[str | None] = mapped_column(String(255))

    product = relationship("Product")
