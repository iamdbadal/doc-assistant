import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ---------------------------------------------------------------------------
# Make the application package importable.
#
# Project structure:
# doc-assistant/
# └── services/
#     └── api/
#         ├── app/
#         └── alembic/
#
# __file__ is:
# services/api/alembic/env.py
#
# Therefore ".." is services/api.
# ---------------------------------------------------------------------------

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from app.db.models import Base
from app.settings import settings

# Alembic Config object
config = context.config


# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata used by Alembic autogenerate
target_metadata = Base.metadata


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


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    # Your application uses asyncpg, so Alembic needs
    # SQLAlchemy's async engine here as well.
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()

    import asyncio

    asyncio.run(run_async_migrations())


def do_run_migrations(connection) -> None:
    """Run migrations using a synchronous SQLAlchemy connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
