import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# =============================================================================
# Make the application package importable
# =============================================================================
#
# Project structure:
#
# doc-assistant/
# ├── alembic.ini
# └── services/
#     └── api/
#         ├── app/
#         └── alembic/
#             └── env.py
#
# This file is:
#
# services/api/alembic/env.py
#
# Therefore ".." points to:
#
# services/api/
#
# Adding that directory to sys.path allows:
#
# from app.db.models import Base
#
# to work when Alembic is executed from the project root.
# =============================================================================

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from app.db.models import Base
from app.settings import settings

# =============================================================================
# Alembic configuration
# =============================================================================

config = context.config


# =============================================================================
# Configure Python logging
# =============================================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =============================================================================
# SQLAlchemy metadata
# =============================================================================
#
# Alembic uses this metadata when generating migrations with:
#
# alembic revision --autogenerate
#
# =============================================================================

target_metadata = Base.metadata


# =============================================================================
# Offline migrations
# =============================================================================


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = settings.database_url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# =============================================================================
# Online migrations
# =============================================================================


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    # -------------------------------------------------------------------------
    # The application uses PostgreSQL + asyncpg.
    #
    # Therefore we create an asynchronous SQLAlchemy engine.
    # -------------------------------------------------------------------------

    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()

    asyncio.run(run_async_migrations())


# =============================================================================
# Run migrations using a synchronous SQLAlchemy connection
# =============================================================================


def do_run_migrations(connection) -> None:
    """Run migrations using a synchronous SQLAlchemy connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


# =============================================================================
# Entry point
# =============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
