import asyncio

from aiokafka import AIOKafkaConsumer
from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.settings import settings
from app.db.session import get_session

router = APIRouter(prefix="/v1", tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))

    consumer = AIOKafkaConsumer(bootstrap_servers=settings.kafka_bootstrap, group_id=None)
    await consumer.start()
    try:
        await asyncio.wait_for(consumer.topics(), timeout=2.0)
    finally:
        await consumer.stop()

    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
