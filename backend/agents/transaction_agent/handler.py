from sqlalchemy import func, select
from kernel.common.database import Session
from .models import StockTransaction

def list_transactions(db: Session, page=1, page_size=20):
    total = db.scalar(select(func.count(StockTransaction.id))) or 0
    items = list(db.scalars(select(StockTransaction).order_by(StockTransaction.id.desc()).offset((page-1)*page_size).limit(page_size)))
    return items, total

def get_product_transactions(db: Session, pid: int):
    return list(db.scalars(select(StockTransaction).where(StockTransaction.product_id == pid).order_by(StockTransaction.id.desc())))

def get_doc_transactions(db: Session, doc_type: str, doc_id: int):
    return list(db.scalars(select(StockTransaction).where(
        StockTransaction.related_doc_type == doc_type, StockTransaction.related_doc_id == doc_id)))

def trace_product(db: Session, pid: int):
    txs = get_product_transactions(db, pid)
    return [{"transaction_no": t.transaction_no, "transaction_type": t.transaction_type,
             "change_quantity": t.change_quantity, "transaction_time": str(t.transaction_time)} for t in txs]
