from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session per request — like Django's request-scoped DB connection."""
    async with AsyncSessionFactory() as session:
        yield session


async def create_tables() -> None:
    """Create all tables directly — only used in development, not in production."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
