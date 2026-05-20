import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.example_data_service import generate_example_data


if __name__ == "__main__":
    result = generate_example_data()
    print(result)
