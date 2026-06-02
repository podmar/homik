import uuid
from datetime import UTC, datetime

from fastapi_users import schemas
from sqlmodel import Field, SQLModel


# fastapi-users-db-sqlalchemy doesn't ship a SQLModel-specific base class —
# SQLAlchemyUserDatabase works with any model that has the right columns.
# We define them explicitly here. SQLModel registers them as SQLAlchemy columns
# under the hood, so the adapter can query them normally.
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]  # "user" is reserved in Postgres

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(max_length=320, unique=True, index=True)
    hashed_password: str = Field(max_length=1024)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    # Nullable until the on_after_register hook creates and assigns a household.
    household_id: int | None = Field(
        default=None, foreign_key="household.id", index=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserRead(schemas.BaseUser[uuid.UUID]):
    household_id: int | None = None


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
