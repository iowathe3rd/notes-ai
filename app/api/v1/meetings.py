from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Meeting, OutboxEvent
from app.db.session import get_session

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_meeting(payload: dict, session: AsyncSession = Depends(get_session)):
    async with session.begin():
        meeting = Meeting(
            tenant_id=payload["tenant_id"],
            title=payload["title"],
        )

        session.add(meeting)
        await session.flush()

        event = OutboxEvent(
            event_type="meeting.created",
            aggregate_id=meeting.meeting_id,
            payload={
                "meeting_id": str(meeting.meeting_id),
                "tenant_id": str(meeting.tenant_id),
                "title": meeting.title,
            },
        )
        session.add(event)

    return {
        "meeting_id": str(meeting.meeting_id),
        "tenant_id": str(meeting.tenant_id),
        "title": meeting.title,
        "status": meeting.status,
        "created_at": meeting.created_at.isoformat(),
        "updated_at": meeting.updated_at.isoformat(),
    }

@router.get("/{meeting_id}")
async def get_meeting(meeting_id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Meeting).where(Meeting.meeting_id == meeting_id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    return {
        "meeting": {
            "meeting_id": str(meeting.meeting_id),
            "tenant_id": str(meeting.tenant_id),
            "title": meeting.title,
            "status": meeting.status,
            "created_at": meeting.created_at.isoformat(),
            "updated_at": meeting.updated_at.isoformat(),
        },
        "artifact": [],
    }