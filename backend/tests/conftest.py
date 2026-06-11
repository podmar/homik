from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import app.database as _db


class _Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    test_database_url: SecretStr


_env = _Env()  # type: ignore[call-arg]

# Replace the app's engine and session factory with test-DB equivalents before
# app.main is imported. All subsequent imports see the patched module globals,
# so every request in tests hits the test DB — not production.
# NullPool creates a fresh connection per operation and never retains one between
# uses — required for async SQLAlchemy tests where each test runs in its own
# event loop. A retained connection would be bound to the loop that created it
# and fail with "Future attached to a different loop" in subsequent tests.
_test_engine = create_async_engine(
    _env.test_database_url.get_secret_value(),
    poolclass=NullPool,
)
_db.engine = _test_engine
_db._session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

from app.main import app  # noqa: E402 — must follow the patch above


@pytest.fixture(autouse=True)
async def clean_db() -> None:
    # Drop and recreate all tables so the schema always reflects the current models,
    # including any constraints added after the test DB was first provisioned.
    # With NullPool each connection is fresh, so this is safe across event loops.
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth(client: AsyncClient) -> dict[str, str]:
    await client.post("/auth/register", json={"email": "alice@test.com", "password": "testpass123"})
    resp = await client.post(
        "/auth/jwt/login", data={"username": "alice@test.com", "password": "testpass123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def other_auth(client: AsyncClient) -> dict[str, str]:
    """Second user in a separate household — for isolation tests."""
    await client.post("/auth/register", json={"email": "bob@test.com", "password": "testpass123"})
    resp = await client.post(
        "/auth/jwt/login", data={"username": "bob@test.com", "password": "testpass123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
