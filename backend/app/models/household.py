from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Household(SQLModel, table=True):
    __tablename__: str = "households"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
