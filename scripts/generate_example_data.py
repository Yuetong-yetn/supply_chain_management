import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BE_DIR = ROOT / "backend"
for p in (str(ROOT), str(BE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from kernel.common.example_data_service import generate_example_data


if __name__ == "__main__":
    result = generate_example_data()
    print("示例数据文件生成完成。")
    print(f"生成目录：{ROOT / 'example'}")
    print(f"处理结果：{result}")
