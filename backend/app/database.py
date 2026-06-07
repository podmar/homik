from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url.get_secret_value()

# pool_pre_ping=True tests each connection before use and reconnects if Neon
# closed it due to inactivity (Neon drops idle connections after ~5 minutes).
engine = create_async_engine(DATABASE_URL, echo=settings.environment == "development", pool_pre_ping=True)

# keeps objects usable after commit (relevant for async sessions)
# class_=AsyncSession uses SQLModel's session subclass, which adds the .exec() method
# that Pylance/Pyright can resolve. SQLAlchemy's default AsyncSession doesn't have it.
_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency — yields one session per request, closed on exit."""
    async with _session_factory() as session:
        yield session


async def create_db_and_tables() -> None:
    """Create every table registered in SQLModel.metadata (runs on startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
