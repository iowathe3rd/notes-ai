
# notes-ai

Небольшой сервис на **FastAPI** с **Postgres** и инфраструктурой для событий (Redpanda/Kafka). В репозитории уже настроены модели SQLAlchemy и миграции Alembic.

## Стек

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- Alembic (миграции)
- Postgres
- Redpanda (Kafka-совместимый брокер) + Redpanda Console

## Быстрый старт (локально)

### 1) Подготовить окружение

Создайте виртуальное окружение и установите зависимости из `pyproject.toml`:

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install -e .
```

### 2) Настроить переменные окружения

Скопируйте пример и отредактируйте при необходимости:

```bash
copy .env.example .env
```

Переменные (ключевые):

- `DATABASE_URL` — строка подключения для приложения (async).
- `DATABASE_URL_SYNC` — строка подключения для Alembic (sync). Alembic читает именно её.
- `KAFKA_BOOTSTRAP` — адрес брокера (по умолчанию `localhost:9092`).

## Инфраструктура через Docker Compose

Поднимет Postgres, Redpanda и Redpanda Console:

```bash
docker compose up -d
```

Полезные порты:

- Postgres: `localhost:5432`
- Kafka (Redpanda): `localhost:9092`
- Redpanda Console: `http://localhost:8080`

> `docker-compose.yml` читает `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` из `.env`.

## Миграции Alembic

Применить миграции:

```bash
alembic upgrade head
```

Создать новую ревизию (пример):

```bash
alembic revision -m "describe change" --autogenerate
```

Важно:

- Миграции используют `DATABASE_URL_SYNC` (sync-драйвер `psycopg`).
- `alembic.ini` не содержит захардкоженного `sqlalchemy.url` — значение задаётся в `alembic/env.py` через env vars.

## Запуск API

Приложение объявлено как `app` в `app/main.py`.

Запуск в dev-режиме:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Проверка:

- `GET /` → `{ "Hello": "World" }`
- Swagger UI: `http://localhost:8000/docs`

## Структура проекта (кратко)

- `app/main.py` — FastAPI приложение
- `app/core/settings.py` — настройки (env vars / `.env`)
- `app/db/models.py` — модели SQLAlchemy (`Meeting`, `OutboxEvent`)
- `alembic/` — миграции

## .env и секреты

Файл `.env` игнорируется git’ом. Держите локальные секреты только там.
