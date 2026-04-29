"""
Alembic Environment Configuration for Neolysis
================================================
Supports async SQLAlchemy (asyncpg) via run_async_migrations().

Connection string is resolved from app.config.settings so that
no credentials are ever hardcoded in this file.

Usage:
    # Generate a new migration (autogenerate from model diff):
    alembic revision --autogenerate -m "add knowledge_graph table"

    # Apply all pending migrations:
    alembic upgrade head

    # Rollback one step:
    alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ── Load app config & models ───────────────────────────────────────────────
# Import all models so their metadata is registered before autogenerate runs
from app.config import settings
import app.models  # noqa: F401 — registers all ORM models
from app.db.session import Base

# ── Alembic Config ─────────────────────────────────────────────────────────
config = context.config

# Inject the DB URL from settings (never from alembic.ini)
config.set_main_option("sqlalchemy.url", settings.get_database_url())

# Set up Python logging from alembic.ini config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


# ── Offline migrations (generate SQL without connecting) ───────────────────
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL scripts without a live DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online async migrations ────────────────────────────────────────────────
def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (required for asyncpg)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration (with live DB connection)."""
    asyncio.run(run_async_migrations())


# ── Execute ────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
