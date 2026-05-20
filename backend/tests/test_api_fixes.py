from app.services.analytics_service import dashboard


def test_supplier_ranking_returns_200(api_client):
    response = api_client.get("/api/suppliers/ranking")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_dashboard_top_stockout_products_excludes_overstock():
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        data = dashboard(session)
        assert all(item["warning_type"] in {"stockout", "critical_stockout"} for item in data["top_stockout_products"])
        assert all(item["warning_type"] == "overstock" for item in data["top_overstock_products"])
    finally:
        session.close()
