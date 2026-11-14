"""Async engine/session lifecycle.

SQLite is supported for local development only; PostgreSQL (asyncpg) is the
authoritative store for anything shared or deployed.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_connect_args: dict[str, object] = {}
if settings.is_sqlite:
    _connect_args["check_same_thread"] = False
    # Ensure the parent directory exists for file-backed SQLite databases.
    prefix = "sqlite+aiosqlite:///"
    if settings.DATABASE_URL.startswith(prefix):
        db_path = settings.DATABASE_URL[len(prefix) :]
        if db_path and ":memory:" not in db_path:
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

if settings.is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
