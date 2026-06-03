import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore[assignment]
    __table_args__ = (sa.UniqueConstraint("household_id", "name", name="uq_category_household_name"),)

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="households.id", index=True)
    name: str
