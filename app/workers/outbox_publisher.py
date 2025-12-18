from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from sqlalchemy import select

from app.core.settings import settings
from app.db.models import OutboxEvent
from app.db.session import SessionFactory, close_engine

logger = logging.getLogger("outbox_publisher")

EVENTS_TOPIC = "meetings.events.v1"
DLQ_TOPIC = "meetings.dlq.v1"


async def _publish_loop(*, poll_interval_s: float = 0.5, batch_size: int = 100, max_attempts: int = 5) -> None:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap,
        value_serializer=lambda v: json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda v: v.encode("utf-8") if v else None,
    )
    await producer.start()
    try:
        while True:
            published_any = False

            async with SessionFactory() as session:
                async with session.begin():
                    stmt = (
                        select(OutboxEvent)
                        .where(OutboxEvent.published_at.is_(None))
                        .order_by(OutboxEvent.created_at)
                        .with_for_update(skip_locked=True)
                        .limit(batch_size)
                    )
                    events = list((await session.execute(stmt)).scalars())

                    for event in events:
                        event.publish_attempts += 1
                        key = str(event.aggregate_id)
                        try:
                            await producer.send_and_wait(EVENTS_TOPIC, event.payload, key=key)
                            event.published_at = datetime.now(timezone.utc)
                            event.last_error = None
                            published_any = True
                        except Exception as exc:  # noqa: BLE001
                            event.last_error = repr(exc)
                            if event.publish_attempts >= max_attempts:
                                # Best-effort dead-letter; after that, mark as published to stop hot looping.
                                dlq_payload = {
                                    "original_event": event.payload,
                                    "attempts": event.publish_attempts,
                                    "last_error": event.last_error,
                                    "dead_lettered_at": datetime.now(timezone.utc).isoformat(),
                                }
                                await producer.send_and_wait(DLQ_TOPIC, dlq_payload, key=key)
                                event.published_at = datetime.now(timezone.utc)
                                published_any = True

            if not published_any:
                await asyncio.sleep(poll_interval_s)

    finally:
        await producer.stop()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        await _publish_loop()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())

