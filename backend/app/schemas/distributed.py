from datetime import datetime

from app.schemas.common import ORMBase


class DistributedSyncLogRead(ORMBase):
    id: int
    node_name: str
    node_type: str
    region: str | None = None
    sync_type: str
    status: str
    checked_records: int
    mismatch_records: int
    started_at: datetime
    finished_at: datetime | None = None
    message: str | None = None
