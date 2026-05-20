from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.exceptions import BusinessException
from app.core.response import page_response, success_response
from app.models.product import Category
from app.schemas.product import CategoryCreate, CategoryRead, CategoryUpdate
from app.utils.pagination import normalize_pagination

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def list_categories(page: int = 1, page_size: int = 20, keyword: str | None = None, db: Session = Depends(get_db_dep)):
    page, page_size = normalize_pagination(page, page_size)
    query = select(Category)
    if keyword:
        query = query.where(Category.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = [CategoryRead.model_validate(item).model_dump() for item in db.scalars(query.offset((page - 1) * page_size).limit(page_size))]
    return page_response(items, total, page, page_size)


@router.post("")
def create_category(payload: CategoryCreate, db: Session = Depends(get_db_dep)):
    item = Category(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(CategoryRead.model_validate(item).model_dump())


@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(Category, category_id)
    if not item:
        raise BusinessException("category not found", 404)
    return success_response(CategoryRead.model_validate(item).model_dump())


@router.put("/{category_id}")
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db_dep)):
    item = db.get(Category, category_id)
    if not item:
        raise BusinessException("category not found", 404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return success_response(CategoryRead.model_validate(item).model_dump())


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db_dep)):
    item = db.get(Category, category_id)
    if not item:
        raise BusinessException("category not found", 404)
    item.is_active = False
    db.commit()
    return success_response(message="deleted")
