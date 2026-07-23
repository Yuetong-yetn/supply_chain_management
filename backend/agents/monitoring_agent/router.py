from fastapi import APIRouter, Depends
from sqlalchemy import text
from kernel.common.database import Session, SessionLocal, get_db, get_database_runtime_profile
from kernel.common.response import success_response

router = APIRouter(prefix="/api", tags=["monitoring"])

@router.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_st = "connected"
    except Exception:
        db_st = "disconnected"
    return success_response({"status": "running", "database": db_st, "app": "Supply Chain Multi-Agent System"})

@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    profile = get_database_runtime_profile(db)
    return success_response({"status": "connected", "dialect": profile["active_dialect"], "database_url_masked": profile["active_database_url_masked"]})

@router.get("/llm/status")
def llm_status():
    from kernel.common.config import get_settings
    s = get_settings()
    return success_response({"provider": s.llm_provider, "model": s.deepseek_model, "available": bool(s.deepseek_api_key_value)})

@router.get("/example/status")
def example_status(db: Session = Depends(get_db)):
    from kernel.common.query_service import get_basic_counts
    counts = get_basic_counts(db)
    return success_response({
        "products": counts["product_count"],
        "suppliers": counts["supplier_count"],
        "warehouses": counts["warehouse_count"],
        "stores": counts["store_count"],
    })

@router.post("/example/load")
def load_example(db: Session = Depends(get_db)):
    return success_response({"loaded": True, "message": "example data loaded"})
