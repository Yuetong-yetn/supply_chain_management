from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InboundOrder(Base):
    __tablename__ = "inbound_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    inbound_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    inbound_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    handled_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255))

    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    handler = relationship("User")
    items = relationship("InboundItem", back_populates="inbound_order", cascade="all, delete-orphan")


class InboundItem(Base):
    __tablename__ = "inbound_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    inbound_order_id: Mapped[int] = mapped_column(ForeignKey("inbound_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_no: Mapped[str | None] = mapped_column(String(50))
    production_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)

    inbound_order = relationship("InboundOrder", back_populates="items")
    product = relationship("Product")
