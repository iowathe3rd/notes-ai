from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import Header, Request

from app.core.settings import settings

CORRELATION_ID_HEADER = "X-Correlation-Id"
TENANT_ID_HEADER = "X-Tenant-Id"


def get_correlation_id(request: Request) -> UUID:
    correlation_id: UUID | None = getattr(request.state, "correlation_id", None)
    return correlation_id or uuid.uuid4()


def get_tenant_id(x_tenant_id: str | None = Header(default=None, alias=TENANT_ID_HEADER)) -> UUID:
    if x_tenant_id:
        return UUID(x_tenant_id)
    if settings.default_tenant_id:
        return settings.default_tenant_id
    return uuid.uuid4()

