from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.config import get_settings
from app.core.response import success_response

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health(db: Session = Depends(get_db_dep)):
    db.execute(text("SELECT 1"))
    return success_response(
        {
            "status": "running",
            "database": "connected",
            "app": get_settings().app_name,
        }
    )
