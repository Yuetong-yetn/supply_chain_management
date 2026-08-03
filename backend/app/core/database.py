"""数据库引擎与会话 — 转发 kernel.common.database，保证 engine/SessionLocal 单例唯一。"""

from kernel.common.database import (
    Base, engine, SessionLocal, get_db, Session,
    get_active_database_url, get_database_dialect_name,
    is_sqlite_bind, get_database_runtime_profile,
)

__all__ = [
    "Base", "engine", "SessionLocal", "get_db", "Session",
    "get_active_database_url", "get_database_dialect_name",
    "is_sqlite_bind", "get_database_runtime_profile",
]
