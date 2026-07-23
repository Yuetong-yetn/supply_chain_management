"""pytest 配置 — 测试基础设施。

测试使用独立的 SQLite 数据库，每次会话自动重建。
"""

import os
import sys

# 在导入其他模块前覆盖 DATABASE_URL
_test_db_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "schema", "test_suite.db",
)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["SQLITE_FALLBACK_URL"] = f"sqlite:///{_test_db_path}"

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from kernel.common.database import Base
from kernel.common.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db():
    """每个测试会话开始时重建数据库。"""
    # 清理已存在的引擎连接，删除旧数据库文件
    db_path = Path(_test_db_path)
    if db_path.exists():
        db_path.unlink()

    # 清理缓存以便重新加载配置
    get_settings.cache_clear()

    # 创建表和引擎
    from kernel.common.database import engine
    Base.metadata.create_all(bind=engine)
    yield
    # 清理
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """提供数据库会话，测试结束后回滚。"""
    from kernel.common.database import SessionLocal
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """提供 FastAPI TestClient。"""
    # 需要先加载主应用
    from main import app
    with TestClient(app) as tc:
        yield tc


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """登录管理员并返回认证头。"""
    response = client.post("/api/users/login", json={
        "username": "admin",
        "password": "admin123",
    })
    if response.status_code != 200:
        pytest.skip("Login failed — seed data may not be loaded")
    data = response.json()
    token = data.get("data", {}).get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
