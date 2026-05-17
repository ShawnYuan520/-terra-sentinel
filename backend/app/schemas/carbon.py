from pydantic import BaseModel
from datetime import datetime


class CarbonReportCreate(BaseModel):
    field_id: str
    period_start: datetime
    period_end: datetime
    straw_amount: float


class CarbonReportOut(BaseModel):
    id: str
    user_id: str
    field_id: str
    period_start: datetime
    period_end: datetime
    straw_amount: float | None
    carbon_amount: float | None
    status: str
    ai_analysis: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CarbonReportListOut(BaseModel):
    total: int
    items: list[CarbonReportOut]