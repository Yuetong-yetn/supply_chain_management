from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReplenishmentRequest(Base):
    __tablename__ = "replenishment_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    request_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    request_reason: Mapped[str | None] = mapped_column(String(255))
    request_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    audit_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    audited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    audit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    generated_outbound_order_id: Mapped[int | None] = mapped_column(Integer)

    store = relationship("Store")
    product = relationship("Product")
