"""仓库相关请求模型。"""

from pydantic import BaseModel


class WarehouseCreate(BaseModel):
    warehouse_code: str; name: str; address: str | None = None
    manager_name: str | None = None; phone: str | None = None
    capacity: int | None = None; status: str | None = None
