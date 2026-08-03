"""位置名称查询 — 替代 user_agent handler 中直接导入 warehouse_agent / store_agent 的 models。"""

from app.core.database import Session


def get_location_name(
    db: Session, location_type: str | None,
    warehouse_id: int | None = None, store_id: int | None = None,
) -> str | None:
    """根据位置类型和 ID 返回位置名称。"""
    if location_type == "warehouse" and warehouse_id:
        from app.models.warehouse import Warehouse
        wh = db.get(Warehouse, warehouse_id)
        return wh.name if wh else None
    elif location_type == "store" and store_id:
        from app.models.store import Store
        st = db.get(Store, store_id)
        return st.name if st else None
    return None
