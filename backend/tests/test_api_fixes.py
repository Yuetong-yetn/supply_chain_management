from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.product import Product
from app.models.store import Store
from app.models.supplier import SupplierProduct
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.analytics_service import build_dashboard_metrics


def test_supplier_ranking_returns_200(api_client):
    response = api_client.get("/api/suppliers/ranking")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_dashboard_top_stockout_products_excludes_overstock():
    session = SessionLocal()
    try:
        data = build_dashboard_metrics(session)
        assert all(item["warning_type"] in {"stockout", "critical_stockout"} for item in data["top_stockout_products"])
        assert all(item["warning_type"] == "overstock" for item in data["top_overstock_products"])
    finally:
        session.close()


def test_create_product_returns_readable_message_when_product_code_is_duplicated(api_client):
    session = SessionLocal()
    try:
        existing = Product(
            product_code=f"PROD-DUP-{uuid4().hex[:6]}",
            name="重复编码测试商品",
            unit="件",
            default_safety_stock=10,
            is_active=True,
        )
        session.add(existing)
        session.commit()
        duplicated_code = existing.product_code
    finally:
        session.close()

    response = api_client.post(
        "/api/products",
        json={
            "product_code": duplicated_code,
            "name": "另一个商品",
            "barcode": f"BAR-{uuid4().hex[:8]}",
            "unit": "件",
            "default_safety_stock": 10,
            "is_active": True,
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == "商品编码已存在，请勿重复填写"


def test_global_exception_handler_hides_internal_details():
    marker = uuid4().hex
    path = f"/__test__/unhandled-{marker}"

    @app.get(path)
    def _raise_unhandled_error():
        raise RuntimeError(f"secret-internal-detail-{marker}")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(path)

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == "服务器内部错误，请稍后重试"
    assert marker not in payload["message"]


def _write_endpoint_seed_data():
    session = SessionLocal()
    try:
        relation = session.query(SupplierProduct).first()
        warehouse = session.query(Warehouse).filter(Warehouse.status == "active").first()
        store = session.query(Store).filter(Store.business_status == "active").first()
        user = session.query(User).filter(User.employee_no == "A1001").first()
        assert relation and warehouse and store and user
        return {
            "supplier_id": relation.supplier_id,
            "product_id": relation.product_id,
            "warehouse_id": warehouse.id,
            "store_id": store.id,
            "user_id": user.id,
            "price": float(relation.supply_price),
        }
    finally:
        session.close()


def test_write_order_endpoints_return_success_instead_of_internal_error(api_client):
    seed = _write_endpoint_seed_data()

    purchase_response = api_client.post(
        "/api/purchase-orders",
        json={
            "supplier_id": seed["supplier_id"],
            "created_by": seed["user_id"],
            "remark": "write endpoint regression",
            "items": [
                {
                    "product_id": seed["product_id"],
                    "purchase_quantity": 1,
                    "purchase_price": seed["price"],
                }
            ],
        },
    )
    assert purchase_response.status_code == 200
    purchase_id = purchase_response.json()["data"]["id"]

    confirm_response = api_client.post(f"/api/purchase-orders/{purchase_id}/confirm")
    assert confirm_response.status_code == 200

    inbound_response = api_client.post(
        "/api/inbound-orders",
        json={
            "supplier_id": seed["supplier_id"],
            "warehouse_id": seed["warehouse_id"],
            "handled_by": seed["user_id"],
            "remark": "write endpoint regression",
            "items": [{"product_id": seed["product_id"], "quantity": 1}],
        },
    )
    assert inbound_response.status_code == 200
    inbound_id = inbound_response.json()["data"]["id"]

    complete_response = api_client.post(f"/api/inbound-orders/{inbound_id}/complete")
    assert complete_response.status_code == 200

    outbound_response = api_client.post(
        "/api/outbound-orders",
        json={
            "source_warehouse_id": seed["warehouse_id"],
            "target_store_id": seed["store_id"],
            "handled_by": seed["user_id"],
            "remark": "write endpoint regression",
            "items": [{"product_id": seed["product_id"], "quantity": 1}],
        },
    )
    assert outbound_response.status_code == 200
    outbound_id = outbound_response.json()["data"]["id"]

    ship_response = api_client.post(f"/api/outbound-orders/{outbound_id}/ship")
    assert ship_response.status_code == 200
