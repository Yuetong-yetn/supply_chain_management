import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.example_data_service import generate_example_data, load_example_data


def ensure_example_data_files() -> None:
    example_dir = get_settings().example_dir_path
    if not example_dir.exists() or not list(example_dir.glob("*.json")):
        generate_example_data()


if __name__ == "__main__":
    print("正在检查并导入示例数据...")
    ensure_example_data_files()
    session = SessionLocal()
    try:
        result = load_example_data(session)
        session.commit()
        print("示例数据导入完成。")
        print(f"处理结果：{result}")
    except Exception:
        session.rollback()
        print("示例数据导入失败，已回滚数据库事务。")
        raise
    finally:
        session.close()
