from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        UniqueConstraint("product_id", "store_id", name="uq_inventory_product_store"),
        CheckConstraint("current_quantity >= 0", name="ck_inventory_current_nonnegative"),
        CheckConstraint("frozen_quantity >= 0", name="ck_inventory_frozen_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_type: Mapped[str] = mapped_column(String(20), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    current_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    frozen_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product")
    warehouse = relationship("Warehouse")
    store = relationship("Store")
