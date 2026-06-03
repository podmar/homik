from datetime import UTC, datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    __tablename__ = "items"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    household_id: int = Field(foreign_key="households.id", index=True)
    name: str
    barcode: str | None = Field(default=None, index=True)
    brand: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    # Nullable: category may be unknown if barcode lookup returns no result.
    category_id: int | None = Field(default=None, foreign_key="categories.id")
    # Nullable: defaults to last used location, which may not exist yet.
    location_id: int | None = Field(default=None, foreign_key="locations.id")
    unit: str
    notes: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    # onupdate fires automatically on every ORM-level UPDATE to this row.
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            nullable=False,
            onupdate=lambda: datetime.now(UTC),
        ),
    )
