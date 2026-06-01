from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.backend import auth_backend
from app.auth.users import fastapi_users
from app.database import create_db_and_tables
import app.models  # noqa: F401 — ensures all table models are registered before create_all
from app.models.user import UserCreate, UserRead
from app.routers import household


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# FastAPI Users generates these routers from the schemas and auth backend.
# /auth/jwt/login and /auth/jwt/logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
# /auth/register
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(household.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
