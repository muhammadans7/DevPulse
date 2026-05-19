import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from app.config import settings
from app.models import api_key, org, repo, user  # noqa: F401

config = context.config # read alembic.ini
fileConfig(config.config_file_name) # activates logging

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection — generates raw SQL instead."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create a fresh async engine for the migration run then dispose it."""
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
