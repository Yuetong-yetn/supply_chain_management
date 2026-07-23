from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from kernel.common.event import Event, event_bus
from .models import PurchaseOrder, PurchaseOrderItem, InboundOrder, InboundItem
from .events import EVENT_INBOUND_COMPLETED

def generate_no(prefix: str, db: Session) -> str:
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    count = (db.scalar(select(func.count(PurchaseOrder.id))) or 0) + 1
    return f"{prefix}{today}{count:04d}"

def create_purchase_order(db: Session, data: dict):
    items_data = data.pop("items", [])
    total = sum(i["purchase_quantity"] * i["purchase_price"] for i in items_data)
    order = PurchaseOrder(order_no=generate_no("PO", db), total_amount=total, status="pending", **data)
    db.add(order); db.flush()
    for i in items_data:
        db.add(PurchaseOrderItem(purchase_order_id=order.id, subtotal_amount=i["purchase_quantity"]*i["purchase_price"], **i))
    db.flush()
    return order

def confirm_purchase_order(db: Session, oid: int):
    o = db.get(PurchaseOrder, oid)
    if not o: raise BusinessException("purchase order not found", 404)
    if o.status != "pending": raise BusinessException("only pending can be confirmed")
    o.status = "confirmed"; db.flush(); return o

def cancel_purchase_order(db: Session, oid: int):
    o = db.get(PurchaseOrder, oid)
    if not o: raise BusinessException("not found", 404)
    o.status = "cancelled"; db.flush(); return o

def complete_inbound(db: Session, iid: int):
    o = db.get(InboundOrder, iid)
    if not o: raise BusinessException("inbound order not found", 404)
    if o.status != "pending": raise BusinessException("only pending can be completed")
    o.status = "completed"
    items = list(db.scalars(select(InboundItem).where(InboundItem.inbound_order_id == iid)))
    db.flush()
    event_bus.publish(Event(type=EVENT_INBOUND_COMPLETED, source="procurement_agent", data={
        "inbound_order_id": o.id, "warehouse_id": o.warehouse_id,
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in items],
        "handled_by": o.handled_by,
        "_db": db,
    }))
    return o
