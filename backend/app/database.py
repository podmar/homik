import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL, echo=False)

_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency — yields one session per request, closed on exit."""
    async with _session_factory() as session:
        yield session


async def create_db_and_tables() -> None:
    """Create every table registered in SQLModel.metadata (runs on startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
