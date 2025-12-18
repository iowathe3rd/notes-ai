from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


EventType = Literal[
    "meeting.created",
    "asset.uploaded",
    "transcription.requested",
    "transcription.completed",
    "summary.generated",
    "actions.extracted",
    "delivery.requested",
    "delivery.sent",
    "pipeline.failed",
]


class EventEnvelope(BaseModel):
    event_id: UUID
    event_type: EventType
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    schema_version: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)

