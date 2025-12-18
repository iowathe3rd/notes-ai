from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_correlation_id, get_tenant_id
from app.db.models import Meeting, OutboxEvent
from app.db.session import get_session
from app.schemas.events import EventEnvelope
from app.schemas.meetings import MeetingCreateRequest, MeetingCreateResponse, MeetingDTO, MeetingGetResponse

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreateRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
    correlation_id: UUID = Depends(get_correlation_id),
) -> MeetingCreateResponse:
    async with session.begin():
        meeting = Meeting(
            tenant_id=tenant_id,
            title=payload.title,
        )

        session.add(meeting)
        await session.flush()

        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="meeting.created",
            occurred_at=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            payload={
                "meeting_id": str(meeting.meeting_id),
                "title": meeting.title,
            },
        )

        event = OutboxEvent(
            event_type=envelope.event_type,
            aggregate_id=meeting.meeting_id,
            payload=envelope.model_dump(mode="json"),
        )
        session.add(event)

    meeting_dto = MeetingDTO(
        meeting_id=meeting.meeting_id,
        tenant_id=meeting.tenant_id,
        title=meeting.title,
        status=meeting.status,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )
    return MeetingCreateResponse(correlation_id=correlation_id, meeting=meeting_dto)


@router.get("/{meeting_id}")
async def get_meeting(
    meeting_id: UUID,
    session: AsyncSession = Depends(get_session),
    correlation_id: UUID = Depends(get_correlation_id),
) -> MeetingGetResponse:
    result = await session.execute(
        select(Meeting).where(Meeting.meeting_id == meeting_id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    meeting_dto = MeetingDTO(
        meeting_id=meeting.meeting_id,
        tenant_id=meeting.tenant_id,
        title=meeting.title,
        status=meeting.status,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )
    return MeetingGetResponse(correlation_id=correlation_id, meeting=meeting_dto, artifacts=[])
