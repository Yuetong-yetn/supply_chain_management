from datetime import datetime

from app.schemas.common import ORMBase


class StockTransactionRead(ORMBase):
    id: int
    transaction_no: str
    product_id: int
    transaction_type: str
    source_location_type: str | None = None
    source_warehouse_id: int | None = None
    source_store_id: int | None = None
    target_location_type: str | None = None
    target_warehouse_id: int | None = None
    target_store_id: int | None = None
    change_quantity: int
    before_quantity: int | None = None
    after_quantity: int | None = None
    transaction_time: datetime
    operated_by: int | None = None
    related_doc_type: str | None = None
    related_doc_id: int | None = None
    remark: str | None = None
