from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from kernel.common.database import get_db, Session
from kernel.common.response import success_response, page_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from .handler import list_warehouses, create_warehouse, get_warehouse

router = APIRouter(prefix="/api", tags=["warehouses"])

class WarehouseCreate(BaseModel):
    warehouse_code: str; name: str; address: str | None = None
    manager_name: str | None = None; phone: str | None = None; capacity: int = 0

@router.get("/warehouses")
def list_route(page: int = Query(1), page_size: int = Query(20), keyword: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total = list_warehouses(db, page, page_size, keyword)
    return page_response(items, total, page, page_size)

@router.post("/warehouses")
def create_route(data: WarehouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(create_warehouse(db, data.model_dump()))

@router.get("/warehouses/{wid}")
def get_route(wid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(get_warehouse(db, wid))
