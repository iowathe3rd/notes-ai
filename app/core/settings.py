from __future__ import annotations

from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""
    database_url_sync: str = ""
    kafka_bootstrap: str = "localhost:9092"
    default_tenant_id: UUID | None = None


settings = Settings()
