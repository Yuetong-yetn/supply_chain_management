from __future__ import annotations

import argparse
from importlib import import_module
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BE_DIR = ROOT / "backend"
for p in (str(ROOT), str(BE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy.schema import CreateTable

from kernel.common.config import get_settings
from kernel.common.database import Base, SessionLocal, engine, get_active_database_url
from agents.user_agent.models import User
from kernel.common.hash_utils import hash_password


MODEL_MODULES = (
    "agents.user_agent.models",
    "agents.product_agent.models",
    "agents.supplier_agent.models",
    "agents.procurement_agent.models",
    "agents.inventory_agent.models",
    "agents.warehouse_agent.models",
    "agents.store_agent.models",
    "agents.fulfillment_agent.models",
    "agents.transaction_agent.models",
    "agents.recommendation_agent.models",
)


def load_model_metadata() -> None:
    for module_name in MODEL_MODULES:
        import_module(module_name)


def export_schema_sql(schema_path: Path) -> None:
    statements = []
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(engine)).strip() + ";\n")
    schema_path.write_text("\n".join(statements), encoding="utf-8")


def export_seed_sql(seed_path: Path) -> None:
    users = [
        ("admin", "A1001", "admin123", "246810", "系统管理员", "admin", True),
        ("buyer", "P1001", "buyer123", "135790", "采购专员", "buyer", True),
        ("warehouse", "W1001", "warehouse123", "975310", "仓库主管", "warehouse_manager", True),
        ("store", "S1001", "store123", "864200", "门店员工", "store_staff", True),
        ("manager", "M1001", "manager123", "112233", "运营经理", "manager", True),
    ]
    lines = []
    for username, employee_no, password, verification_code, real_name, role, is_verified in users:
        lines.append(
            "INSERT INTO users "
            "(username, employee_no, password_hash, verification_code_hash, real_name, role, is_active, is_verified) "
            "VALUES "
            f"('{username}', '{employee_no}', '{hash_password(password)}', '{hash_password(verification_code)}', "
            f"'{real_name}', '{role}', 1, {1 if is_verified else 0});"
        )
    seed_path.write_text("\n".join(lines), encoding="utf-8")


def init_db(rebuild: bool = False) -> None:
    load_model_metadata()
    settings = get_settings()
    settings.schema_dir_path.mkdir(parents=True, exist_ok=True)
    active_database_url = get_active_database_url()
    active_is_sqlite = active_database_url.startswith("sqlite")
    if active_is_sqlite:
        database_path = settings.resolve_sqlite_path(active_database_url)
        if rebuild and database_path.exists():
            engine.dispose()
            database_path.unlink()
    elif rebuild:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    if active_is_sqlite:
        export_schema_sql(settings.schema_dir_path / "schema.sql")
        export_seed_sql(settings.schema_dir_path / "seed.sql")
    session = SessionLocal()
    try:
        existing = {row.username for row in session.query(User).all()}
        seed_users = [
            {
                "username": "admin",
                "employee_no": "A1001",
                "password": "admin123",
                "verification_code": "246810",
                "real_name": "系统管理员",
                "role": "admin",
                "is_verified": True,
            },
            {
                "username": "buyer",
                "employee_no": "P1001",
                "password": "buyer123",
                "verification_code": "135790",
                "real_name": "采购专员",
                "role": "buyer",
                "is_verified": True,
            },
            {
                "username": "warehouse",
                "employee_no": "W1001",
                "password": "warehouse123",
                "verification_code": "975310",
                "real_name": "仓库主管",
                "role": "warehouse_manager",
                "is_verified": True,
            },
            {
                "username": "store",
                "employee_no": "S1001",
                "password": "store123",
                "verification_code": "864200",
                "real_name": "门店员工",
                "role": "store_staff",
                "is_verified": True,
            },
            {
                "username": "manager",
                "employee_no": "M1001",
                "password": "manager123",
                "verification_code": "112233",
                "real_name": "运营经理",
                "role": "manager",
                "is_verified": True,
            },
        ]
        for item in seed_users:
            if item["username"] not in existing:
                session.add(
                    User(
                        username=item["username"],
                        employee_no=item["employee_no"],
                        password_hash=hash_password(item["password"]),
                        verification_code_hash=hash_password(item["verification_code"]),
                        real_name=item["real_name"],
                        role=item["role"],
                        is_active=True,
                        is_verified=item["is_verified"],
                    )
                )
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    init_db(rebuild=args.rebuild)
