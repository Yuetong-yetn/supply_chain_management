from fastapi import APIRouter, Depends, Query
from kernel.common.database import get_db, Session
from kernel.common.response import success_response
from kernel.common.auth import get_current_user
from agents.user_agent.models import User
from sqlalchemy import select
from .handler import generate_recommendations, set_adoption_status
from .models import AIRecommendation

router = APIRouter(prefix="/api", tags=["recommendations"])

@router.post("/recommendations/generate")
def generate(store_id: int = Query(None), enhance_with_llm: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recs = generate_recommendations(db, store_id, enhance_with_llm)
    return success_response({"count": len(recs)})

@router.get("/recommendations")
def list_recs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(list(db.scalars(select(AIRecommendation))))

@router.get("/recommendations/store/{sid}")
def store_recs(sid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(list(db.scalars(select(AIRecommendation).where(AIRecommendation.store_id == sid))))

@router.post("/recommendations/{rid}/accept")
def accept(rid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(set_adoption_status(db, rid, "accepted"))

@router.post("/recommendations/{rid}/reject")
def reject(rid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(set_adoption_status(db, rid, "rejected"))
