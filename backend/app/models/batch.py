from datetime import UTC, date, datetime, timedelta

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Batch(SQLModel, table=True):
    __tablename__ = "batches"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    # Denormalized from Item for query-level household isolation — every batch query can filter
    # directly on household_id without joining through items.
    household_id: int = Field(foreign_key="households.id", index=True)
    item_id: int = Field(foreign_key="items.id", index=True)
    quantity: int = Field(sa_column=sa.Column(sa.Integer, sa.CheckConstraint("quantity > 0"), nullable=False))
    # Defaults to approximately +12 months from today.
    # Month + year precision only — the day component is not shown in the UI.
    expiry_date: date = Field(
        default_factory=lambda: date.today() + timedelta(days=365)
    )
    location_id: int = Field(foreign_key="locations.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
