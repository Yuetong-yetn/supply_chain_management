from kernel.common.database import engine, get_database_dialect_name, get_database_runtime_profile

def check_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "running", "database": db_status, "app": "Supply Chain Multi-Agent System"}

def check_db():
    from sqlalchemy import text
    profile = get_database_runtime_profile()
    return {"status": "connected", "dialect": profile["active_dialect"], "database_url_masked": profile["active_database_url_masked"]}
