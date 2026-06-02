from sqlmodel import Field, SQLModel


class Location(SQLModel, table=True):
    __tablename__ = "locations"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="households.id", index=True)
    name: str
