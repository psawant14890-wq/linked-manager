import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    draft_type: str
    content: str
    message_id: uuid.UUID | None
    created_at: datetime


class WeeklyReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period_start: datetime
    period_end: datetime
    content: str
    generated_at: datetime


class WeeklyReportGenerateRequest(BaseModel):
    period_days: int = 7
