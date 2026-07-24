from datetime import datetime
from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from kernel.common.event import Event, event_bus
from .models import ReplenishmentRequest, OutboundOrder, OutboundItem
from .events import *

def generate_no(prefix: str, db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    count = (db.scalar(select(func.count(ReplenishmentRequest.id))) or 0) + 1
    return f"{prefix}{today}{count:04d}"

def create_request(db: Session, data: dict):
    r = ReplenishmentRequest(request_no=generate_no("RR", db), audit_status="pending", **data)
    db.add(r); db.flush(); return r

def approve_request(db: Session, rid: int, audited_by: int):
    r = db.get(ReplenishmentRequest, rid)
    if not r: raise BusinessException("not found", 404)
    if r.audit_status != "pending": raise BusinessException("only pending can be approved")
    r.audit_status = "approved"; r.audited_by = audited_by; r.audit_time = datetime.utcnow()
    db.flush()
    event_bus.publish(Event(type=EVENT_REPLENISHMENT_APPROVED, source="fulfillment_agent", data={"request_id": rid}))
    return r

def reject_request(db: Session, rid: int, audited_by: int):
    r = db.get(ReplenishmentRequest, rid)
    if not r: raise BusinessException("not found", 404)
    if r.audit_status != "pending": raise BusinessException("only pending can be rejected")
    r.audit_status = "rejected"; r.audited_by = audited_by; r.audit_time = datetime.utcnow()
    db.flush(); return r

def convert_to_outbound(db: Session, rid: int, source_warehouse_id: int | None = None, handled_by: int = 1):
    r = db.get(ReplenishmentRequest, rid)
    if not r: raise BusinessException("not found", 404)
    if r.audit_status != "approved": raise BusinessException("only approved can convert")
    if r.generated_outbound_order_id: raise BusinessException("already converted")
    if source_warehouse_id is None:
        from kernel.common.query_service import find_warehouse_with_available_stock

        source_warehouse_id = find_warehouse_with_available_stock(db, r.product_id, r.request_quantity)
        if not source_warehouse_id:
            raise BusinessException("no warehouse has enough available inventory")
    o = OutboundOrder(outbound_no=generate_no("OUT", db), source_warehouse_id=source_warehouse_id,
                       target_store_id=r.store_id, handled_by=handled_by,
                       source_request_id=r.id, status="pending")
    db.add(o); db.flush()
    db.add(OutboundItem(outbound_order_id=o.id, product_id=r.product_id, quantity=r.request_quantity))
    r.generated_outbound_order_id = o.id
    db.flush()
    event_bus.publish(Event(type=EVENT_REPLENISHMENT_CONVERTED, source="fulfillment_agent",
                            data={"outbound_order_id": o.id, "request_id": rid}))
    return o

def ship_order(db: Session, oid: int):
    o = db.get(OutboundOrder, oid)
    if not o: raise BusinessException("not found", 404)
    if o.status != "pending": raise BusinessException("only pending can ship")
    o.status = "shipped"; db.flush()
    items = list(db.scalars(select(OutboundItem).where(OutboundItem.outbound_order_id == oid)))
    event_bus.publish(Event(type=EVENT_OUTBOUND_SHIPPED, source="fulfillment_agent", data={
        "order_id": o.id, "warehouse_id": o.source_warehouse_id, "store_id": o.target_store_id,
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in items],
        "_db": db,
    }))
    return o

def sign_order(db: Session, oid: int):
    o = db.get(OutboundOrder, oid)
    if not o: raise BusinessException("not found", 404)
    if o.status != "shipped": raise BusinessException("only shipped can sign")
    o.status = "signed"; db.flush()
    items = list(db.scalars(select(OutboundItem).where(OutboundItem.outbound_order_id == oid)))
    event_bus.publish(Event(type=EVENT_OUTBOUND_SIGNED, source="fulfillment_agent", data={
        "order_id": o.id, "warehouse_id": o.source_warehouse_id, "store_id": o.target_store_id,
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in items],
        "_db": db,
    }))
    return o

def cancel_order(db: Session, oid: int):
    o = db.get(OutboundOrder, oid)
    if not o: raise BusinessException("not found", 404)
    if o.status in ("shipped", "signed"): raise BusinessException("cannot cancel shipped/signed order")
    o.status = "cancelled"; db.flush(); return o
