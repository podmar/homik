from datetime import UTC, date, datetime, timedelta

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Batch(SQLModel, table=True):
    __tablename__ = "batches"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id", index=True)
    quantity: int
    # Defaults to approximately +12 months from today.
    # Month + year precision only — the day component is not shown in the UI.
    expiry_date: date = Field(
        default_factory=lambda: date.today() + timedelta(days=365)
    )
    # Nullable: location is prefilled in the UI from the last batch, but may be unset on first use.
    location_id: int | None = Field(default=None, foreign_key="locations.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
