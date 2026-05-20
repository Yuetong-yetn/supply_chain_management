from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OutboundOrder(Base):
    __tablename__ = "outbound_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    outbound_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    source_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    target_store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    outbound_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    handled_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    source_request_id: Mapped[int | None] = mapped_column(ForeignKey("replenishment_requests.id"))
    remark: Mapped[str | None] = mapped_column(String(255))

    source_warehouse = relationship("Warehouse")
    target_store = relationship("Store")
    handler = relationship("User")
    items = relationship("OutboundItem", back_populates="outbound_order", cascade="all, delete-orphan")


class OutboundItem(Base):
    __tablename__ = "outbound_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    outbound_order_id: Mapped[int] = mapped_column(ForeignKey("outbound_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_no: Mapped[str | None] = mapped_column(String(50))

    outbound_order = relationship("OutboundOrder", back_populates="items")
    product = relationship("Product")
