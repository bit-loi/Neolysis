"""
Neolysis — Database Session & Engine
======================================
Async SQLAlchemy engine using asyncpg driver.

Features:
  - Connection pooling (pool_size=10, max_overflow=20)
  - Keepalive background task: pings DB every 5 minutes to prevent
    Supabase free-tier auto-pause (starts on app startup)
  - Graceful connection error handling

Exposed:
  - engine            : AsyncEngine
  - AsyncSessionLocal : async_sessionmaker
  - Base              : DeclarativeBase (shared metadata)
  - get_db            : FastAPI dependency yielding AsyncSession
  - start_keepalive   : Start the background keepalive coroutine
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from loguru import logger

from app.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────

engine: AsyncEngine = create_async_engine(
    settings.get_database_url(),
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,       # Validates connections before use
    pool_recycle=3600,        # Recycle connections every hour
    connect_args={
        # asyncpg-specific TCP keepalive settings
        "server_settings": {
            "application_name": "neolysis_api",
        },
    },
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ── Declarative Base ───────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all ORM models."""
    pass


# ── Dependency ─────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session and handles cleanup.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Keepalive ──────────────────────────────────────────────────────────────

_keepalive_task: asyncio.Task | None = None


async def _keepalive_loop(interval: int = 300) -> None:
    """
    Background coroutine that pings the database every `interval` seconds.

    Prevents Supabase free-tier projects from auto-pausing due to inactivity.
    """
    while True:
        await asyncio.sleep(interval)
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            logger.debug("DB keepalive ping: OK")
        except Exception as e:
            logger.warning(f"DB keepalive ping failed: {e}")


def start_keepalive() -> None:
    """
    Schedule the DB keepalive background task.
    Call from app lifespan startup.
    """
    global _keepalive_task
    interval = settings.DB_KEEPALIVE_INTERVAL_SECONDS
    _keepalive_task = asyncio.create_task(_keepalive_loop(interval))
    logger.info(f"DB keepalive started (interval={interval}s)")


def stop_keepalive() -> None:
    """Cancel the keepalive task on shutdown."""
    global _keepalive_task
    if _keepalive_task and not _keepalive_task.done():
        _keepalive_task.cancel()
        logger.info("DB keepalive stopped")
