from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    keyword: str | None = None


class MessageSchema(BaseModel):
    message: str = "ok"


class IdResponse(ORMBase):
    id: int


class DateRange(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


JsonDict = dict[str, Any]
DecimalField = Field(default=Decimal("0.00"), json_schema_extra={"example": "12.50"})
