from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app.core.settings import settings
from app.db.models import Meeting, MeetingStatus, ProcessedEvent
from app.db.session import SessionFactory, close_engine
from app.schemas.events import EventEnvelope

logger = logging.getLogger("meetings_worker")

EVENTS_TOPIC = "meetings.events.v1"
DLQ_TOPIC = "meetings.dlq.v1"
CONSUMER_NAME = "meetings_worker"


async def _handle_event(envelope: EventEnvelope) -> None:
    async with SessionFactory() as session:
        async with session.begin():
            processed = ProcessedEvent(consumer_name=CONSUMER_NAME, event_id=envelope.event_id)
            session.add(processed)
            try:
                await session.flush()
            except IntegrityError:
                # Already processed (idempotency)
                return

            if envelope.event_type == "meeting.created":
                meeting_id = envelope.payload.get("meeting_id")
                if not meeting_id:
                    raise ValueError("meeting_id missing in payload")
                meeting_uuid = UUID(str(meeting_id))

                await session.execute(
                    update(Meeting)
                    .where(Meeting.meeting_id == meeting_uuid)
                    .values(status=MeetingStatus.queued)
                )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    consumer = AIOKafkaConsumer(
        EVENTS_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap,
        group_id="notes-ai-workers",
        enable_auto_commit=False,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap,
        value_serializer=lambda v: json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
    )

    await consumer.start()
    await producer.start()
    try:
        async for msg in consumer:
            try:
                envelope = EventEnvelope.model_validate(msg.value)
                await _handle_event(envelope)
                await consumer.commit()
            except Exception as exc:  # noqa: BLE001
                # Non-retriable errors -> DLQ (best effort), then commit offset to avoid poison-pill loops.
                try:
                    await producer.send_and_wait(
                        DLQ_TOPIC,
                        {"error": repr(exc), "original": msg.value},
                    )
                finally:
                    await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())
