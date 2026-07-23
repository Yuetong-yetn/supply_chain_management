from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import list_stores, create_store, get_store

router = APIRouter(prefix="/api", tags=["stores"])

class StoreCreate(BaseModel):
    store_code: str; name: str; region: str | None = None; address: str | None = None
    longitude: float | None = None; latitude: float | None = None
    contact_person: str | None = None; phone: str | None = None

@router.get("/stores")
def list_route(page: int = Query(1), page_size: int = Query(20), keyword: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total = list_stores(db, page, page_size, keyword)
    return page_response(items, total, page, page_size)

@router.post("/stores")
def create_route(data: StoreCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_store(db, data.model_dump()))

@router.get("/stores/{sid}")
def get_route(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_store(db, sid))
