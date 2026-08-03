from fastapi import APIRouter, Depends, Query
from app.core.database import get_db, Session
from app.core.response import success_response, page_response
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.warehouses import WarehouseCreate
from app.services.warehouse_service import list_warehouses, create_warehouse, get_warehouse

router = APIRouter(prefix="/api", tags=["warehouses"])


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
