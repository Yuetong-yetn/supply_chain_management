from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.response import success_response
from app.services.example_data_service import generate_example_data, get_example_status, load_example_data

router = APIRouter(prefix="/api/example", tags=["example"])


@router.post("/generate")
def generate_example_dataset():
    return success_response(generate_example_data())


@router.post("/load")
def load_example_dataset(db: Session = Depends(get_db_dep)):
    try:
        result = load_example_data(db)
        db.commit()
        return success_response(result)
    except Exception:
        db.rollback()
        raise


@router.get("/status")
def get_example_data_status(db: Session = Depends(get_db_dep)):
    return success_response(get_example_status(db))
