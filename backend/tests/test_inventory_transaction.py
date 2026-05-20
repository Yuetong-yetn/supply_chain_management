from app.core.database import SessionLocal
from app.models.inbound import InboundItem, InboundOrder
from app.models.inventory import Inventory
from app.models.transaction import StockTransaction
from app.services.inbound_service import complete_inbound_order


def test_inbound_complete_updates_inventory_and_transactions():
    session = SessionLocal()
    try:
        order = session.query(InboundOrder).filter_by(status="pending").first()
        assert order is not None
        item = session.query(InboundItem).filter_by(inbound_order_id=order.id).first()
        before = session.query(Inventory).filter_by(product_id=item.product_id, warehouse_id=order.warehouse_id).first()
        before_qty = before.current_quantity if before else 0
        complete_inbound_order(session, order.id)
        session.commit()
        after = session.query(Inventory).filter_by(product_id=item.product_id, warehouse_id=order.warehouse_id).one()
        assert after.current_quantity >= before_qty + item.quantity
        assert session.query(StockTransaction).filter_by(related_doc_type="inbound_order", related_doc_id=order.id).count() > 0
    finally:
        session.close()


def test_inbound_failure_rolls_back():
    session = SessionLocal()
    try:
        order = session.query(InboundOrder).filter_by(status="pending").first()
        order.status = "completed"
        session.flush()
        try:
            complete_inbound_order(session, order.id)
        except Exception:
            session.rollback()
        refreshed = session.get(InboundOrder, order.id)
        assert refreshed.status == "pending"
    finally:
        session.close()
