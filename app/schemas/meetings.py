from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import MeetingStatus
from app.schemas.common import ResponseEnvelope


class MeetingCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)


class MeetingDTO(BaseModel):
    meeting_id: UUID
    tenant_id: UUID
    title: str
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime


class MeetingCreateResponse(ResponseEnvelope):
    meeting: MeetingDTO


class MeetingGetResponse(ResponseEnvelope):
    meeting: MeetingDTO
    artifacts: list[dict] = Field(default_factory=list)
