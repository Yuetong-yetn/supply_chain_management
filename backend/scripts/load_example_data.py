import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.services.example_data_service import load_example_data


if __name__ == "__main__":
    session = SessionLocal()
    try:
        result = load_example_data(session)
        session.commit()
        print(result)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
