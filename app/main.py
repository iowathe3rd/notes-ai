from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.meetings import router as meetings_router
from app.core.correlation import CorrelationIdMiddleware
from app.db.session import close_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_engine()


app = FastAPI(lifespan=lifespan, title="Notes AI", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(meetings_router)
