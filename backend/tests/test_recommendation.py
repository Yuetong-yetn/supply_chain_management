from app.core.database import SessionLocal
from app.models.recommendation import AIRecommendation
from app.services.recommendation_service import generate_recommendations


def test_recommendation_generate():
    session = SessionLocal()
    try:
        items = generate_recommendations(session)
        session.commit()
        assert len(items) > 0
        rec = session.query(AIRecommendation).first()
        assert rec.recommended_quantity >= 0
        assert rec.risk_level in {"low", "medium", "high"}
        assert "门店" in rec.reason
        assert rec.llm_provider == "rule" or rec.reason_enhanced is not None or rec.llm_used is False
    finally:
        session.close()
