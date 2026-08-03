"""门店相关请求模型。"""

from pydantic import BaseModel


class StoreCreate(BaseModel):
    store_code: str; name: str; region: str | None = None; address: str | None = None
    longitude: float | None = None; latitude: float | None = None
    contact_person: str | None = None; phone: str | None = None
