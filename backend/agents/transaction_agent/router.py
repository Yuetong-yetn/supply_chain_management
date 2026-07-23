from fastapi import APIRouter, Depends, Query
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import list_transactions, get_product_transactions, get_doc_transactions, trace_product

router = APIRouter(prefix="/api", tags=["transactions"])

@router.get("/transactions")
def list_tx(page: int = Query(1), page_size: int = Query(20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total = list_transactions(db, page, page_size)
    return page_response(items, total, page, page_size)

@router.get("/transactions/product/{pid}")
def product_tx(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_product_transactions(db, pid))

@router.get("/transactions/doc/{doc_type}/{doc_id}")
def doc_tx(doc_type: str, doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_doc_transactions(db, doc_type, doc_id))

@router.get("/transactions/product/{pid}/trace")
def trace(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(trace_product(db, pid))
