from datetime import datetime
from sqlalchemy import func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from kernel.common.event import Event, event_bus
from .models import Inventory
from .events import EVENT_STOCK_INCREASED, EVENT_STOCK_DECREASED, EVENT_WARNING_TRIGGERED

def get_available(inv: Inventory) -> int:
    return int(inv.current_quantity or 0) - int(inv.frozen_quantity or 0)

def get_or_create(db: Session, product_id: int, location_type: str, warehouse_id=None, store_id=None):
    q = select(Inventory).where(
        Inventory.product_id == product_id, Inventory.location_type == location_type,
        Inventory.warehouse_id == warehouse_id, Inventory.store_id == store_id,
    )
    inv = db.scalar(q)
    if inv: return inv
    inv = Inventory(product_id=product_id, location_type=location_type,
                    warehouse_id=warehouse_id, store_id=store_id)
    db.add(inv); db.flush(); return inv

def increase_stock(db: Session, product_id: int, location_type: str, quantity: int,
                   warehouse_id=None, store_id=None, operator_id=None, transaction_type="adjust",
                   related_doc_type=None, related_doc_id=None):
    inv = get_or_create(db, product_id, location_type, warehouse_id, store_id)
    before = inv.current_quantity
    inv.current_quantity += quantity
    inv.last_updated_at = datetime.utcnow()
    db.flush()
    event_bus.publish(Event(type=EVENT_STOCK_INCREASED, source="inventory_agent", data={
        "product_id": product_id, "location_type": location_type, "warehouse_id": warehouse_id,
        "store_id": store_id, "change_quantity": quantity, "before": before, "after": inv.current_quantity,
        "operator_id": operator_id, "transaction_type": transaction_type,
        "related_doc_type": related_doc_type, "related_doc_id": related_doc_id,
        "_db": db,
    }))
    return inv

def decrease_stock(db: Session, product_id: int, location_type: str, quantity: int,
                   warehouse_id=None, store_id=None, operator_id=None, transaction_type="adjust",
                   related_doc_type=None, related_doc_id=None):
    inv = get_or_create(db, product_id, location_type, warehouse_id, store_id)
    available = get_available(inv)
    if available < quantity:
        raise BusinessException("库存不足")
    before = inv.current_quantity
    inv.current_quantity -= quantity
    inv.last_updated_at = datetime.utcnow()
    db.flush()
    event_bus.publish(Event(type=EVENT_STOCK_DECREASED, source="inventory_agent", data={
        "product_id": product_id, "location_type": location_type, "warehouse_id": warehouse_id,
        "store_id": store_id, "change_quantity": -quantity, "before": before, "after": inv.current_quantity,
        "operator_id": operator_id, "transaction_type": transaction_type,
        "related_doc_type": related_doc_type, "related_doc_id": related_doc_id,
        "_db": db,
    }))
    return inv

def get_warnings(db: Session):
    inventories = list(db.scalars(select(Inventory)))
    warnings = []
    for inv in inventories:
        wt = None
        if inv.current_quantity <= inv.safety_stock * 0.5: wt = "critical_stockout"
        elif inv.current_quantity <= inv.safety_stock: wt = "stockout"
        elif inv.current_quantity >= max(inv.max_stock, inv.safety_stock * 4): wt = "overstock"
        if wt: warnings.append({
            "product_id": inv.product_id, "location_type": inv.location_type,
            "current_quantity": inv.current_quantity, "safety_stock": inv.safety_stock,
            "max_stock": inv.max_stock, "warning_type": wt, "available_quantity": get_available(inv),
        })
    return warnings

def get_summary(db: Session):
    items = list(db.scalars(select(Inventory)))
    return {
        "total_inventory_quantity": sum(i.current_quantity for i in items),
        "warehouse_inventory_quantity": sum(i.current_quantity for i in items if i.location_type == "warehouse"),
        "store_inventory_quantity": sum(i.current_quantity for i in items if i.location_type == "store"),
        "warning_count": len(get_warnings(db)),
        "inventory_record_count": len(items),
    }

def adjust_stock(db: Session, product_id: int, location_type: str, new_quantity: int,
                 warehouse_id=None, store_id=None, operator_id=None, remark=""):
    if new_quantity < 0: raise BusinessException("new_quantity cannot be negative")
    inv = get_or_create(db, product_id, location_type, warehouse_id, store_id)
    before = inv.current_quantity
    inv.current_quantity = new_quantity
    inv.last_updated_at = datetime.utcnow()
    db.flush()
    event_bus.publish(Event(type=EVENT_STOCK_INCREASED if new_quantity >= before else EVENT_STOCK_DECREASED,
                            source="inventory_agent", data={}))
    return inv
