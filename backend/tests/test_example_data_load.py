import json

from app.core.database import SessionLocal
from app.models.analytics import MonthlySalesFact
from app.models.inventory import Inventory
from app.models.product import Category, Product
from app.models.supplier import Supplier
from app.models.user import User
from app.services.example_data_service import generate_example_data, load_example_data


def test_example_data_load():
    result = generate_example_data()
    assert result["products.json"] >= 60
    assert result["suppliers.json"] >= 12
    session = SessionLocal()
    try:
        stats = load_example_data(session)
        session.commit()
        assert stats["categories"] > 0
        assert session.query(Supplier).count() > 0
        assert session.query(Product).count() > 0
        assert session.query(Category).count() > 0
        assert session.query(MonthlySalesFact).count() > 0
        assert session.query(Inventory).count() > 0
        user = session.query(User).filter_by(username="admin").one()
        assert user.password_hash != "admin123"
    finally:
        session.close()
