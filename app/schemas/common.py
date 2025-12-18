from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ResponseEnvelope(BaseModel):
    correlation_id: UUID = Field(..., description="Request correlation id")

