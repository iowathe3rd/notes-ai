from __future__ import annotations

import uuid
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.api.deps import CORRELATION_ID_HEADER


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        raw = request.headers.get(CORRELATION_ID_HEADER)
        correlation_id: UUID
        try:
            correlation_id = UUID(raw) if raw else uuid.uuid4()
        except ValueError:
            correlation_id = uuid.uuid4()

        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = str(correlation_id)
        return response

