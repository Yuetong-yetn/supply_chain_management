import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.cache import cache
from app.core.config import get_settings
from scripts.init_db import init_db
from app.core.database import SessionLocal
from app.main import app
from app.services.example_data_service import generate_example_data, load_example_data


def pytest_sessionstart(session):
    init_db(rebuild=True)
    generate_example_data()
    db = SessionLocal()
    try:
        load_example_data(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    cache.clear()
    yield
    cache.clear()
    get_settings.cache_clear()


@pytest.fixture
def api_client():
    return TestClient(app)
