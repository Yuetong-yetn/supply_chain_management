"""数据库引擎与会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from kernel.common.config import get_settings

settings = get_settings()

# ---------- metadata + declarative base ----------

metadata = None  # 由各 Agent 的模型自行注册到 Base.metadata


class Base(DeclarativeBase):
    pass


# ---------- engine ----------


def _build_connect_args(database_url: str) -> dict[str, object]:
    backend_name = make_url(database_url).get_backend_name()
    if backend_name == "sqlite":
        return {"check_same_thread": False}
    if backend_name == "mysql":
        return {"connect_timeout": settings.database_connect_timeout_seconds}
    return {}


def _normalize_database_url(database_url: str) -> str:
    if make_url(database_url).get_backend_name() != "sqlite":
        return database_url
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        return database_url
    sqlite_path = settings.resolve_sqlite_path(database_url)
    return f"sqlite:///{sqlite_path.as_posix()}"


def _build_engine(database_url: str) -> Engine:
    normalized_url = _normalize_database_url(database_url)
    return create_engine(
        normalized_url,
        connect_args=_build_connect_args(normalized_url),
        pool_pre_ping=True,
        future=True,
    )


def _probe_engine(candidate_engine: Engine) -> None:
    with candidate_engine.connect() as connection:
        connection.execute(text("SELECT 1"))


preferred_database_url = settings.database_url


def _resolve_runtime_engine() -> tuple[Engine, str, bool]:
    active_preferred_url = _normalize_database_url(preferred_database_url)
    candidate_engine = _build_engine(active_preferred_url)
    preferred_backend = make_url(preferred_database_url).get_backend_name()
    if preferred_backend == "sqlite":
        return candidate_engine, active_preferred_url, False
    try:
        _probe_engine(candidate_engine)
        return candidate_engine, active_preferred_url, False
    except Exception:
        candidate_engine.dispose()
        active_fallback_url = _normalize_database_url(settings.sqlite_fallback_url)
        fallback_engine = _build_engine(active_fallback_url)
        _probe_engine(fallback_engine)
        return fallback_engine, active_fallback_url, True


engine, active_database_url, using_sqlite_fallback = _resolve_runtime_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    if engine.dialect.name != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# ---------- helpers ----------


def get_database_dialect_name(bind: Session | Engine | None = None) -> str:
    target = bind.get_bind() if isinstance(bind, Session) else bind or engine
    return target.dialect.name


def is_sqlite_bind(bind: Session | Engine | None = None) -> bool:
    return get_database_dialect_name(bind) == "sqlite"


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_active_database_url() -> str:
    """返回当前激活的数据库连接 URL。"""
    return active_database_url


def get_database_runtime_profile(db: Session | None = None) -> dict[str, str]:
    """返回当前数据库运行时信息（方言、脱敏后的 URL）。"""
    dialect_name = engine.dialect.name if engine else "unknown"
    # 脱敏：隐藏 URL 中的密码
    masked = active_database_url
    if "@" in masked:
        # mysql+pymysql://user:password@host/db → mysql+pymysql://user:***@host/db
        prefix, rest = masked.split("@", 1)
        if "://" in prefix:
            scheme, cred = prefix.split("://", 1)
            if ":" in cred:
                user, _ = cred.split(":", 1)
                masked = f"{scheme}://{user}:***@{rest}"
    return {
        "active_dialect": dialect_name,
        "active_database_url_masked": masked,
    }
