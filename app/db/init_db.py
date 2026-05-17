from app.db.session import create_tables


async def init_db() -> None:
    """Run on app startup to ensure DB is reachable and tables exist in development."""
    await create_tables()
