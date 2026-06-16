from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Field, SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.users import current_active_user
from app.database import get_session
from app.models.batch import Batch
from app.models.item import Item
from app.models.location import Location
from app.models.user import User

# No prefix — batch endpoints span two URL patterns (/items/{id}/batches and /batches/{id}).
router = APIRouter(tags=["batches"])


class BatchRead(SQLModel):
    id: int
    item_id: int
    quantity: int
    expiry_date: date
    location_id: int
    created_at: datetime


class BatchCreate(SQLModel):
    quantity: int = Field(gt=0)
    # Both fields are optional: server resolves defaults if not provided.
    expiry_date: date | None = None
    location_id: int | None = None


class BatchUpdate(SQLModel):
    quantity: int | None = Field(default=None, gt=0)
    expiry_date: date | None = None
    location_id: int | None = None


class BatchAdjust(SQLModel):
    # Positive = scan in (add stock), negative = scan out (use stock).
    delta: int


async def _default_location_id(session: AsyncSession, household_id: int) -> int | None:
    """Return last-used location for this household, or fall back to first seeded location."""
    last = (
        await session.exec(
            select(Batch.location_id)
            .where(Batch.household_id == household_id)
            # col() needed so Pyright treats created_at as a column expression, not a datetime.
            .order_by(col(Batch.created_at).desc())
            .limit(1)
        )
    ).first()
    if last is not None:
        return last
    first_loc = (
        await session.exec(
            select(Location)
            .where(Location.household_id == household_id)
            # col() needed so Pyright treats id as a column expression, not int | None.
            .order_by(col(Location.id))
            .limit(1)
        )
    ).first()
    return first_loc.id if first_loc is not None else None


@router.get("/items/{item_id}/batches")
async def list_item_batches(
    item_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[BatchRead]:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    item = await session.get(Item, item_id)
    if item is None or item.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await session.exec(
        select(Batch).where(Batch.item_id == item_id).order_by(col(Batch.expiry_date))
    )
    return [BatchRead.model_validate(b) for b in result.all()]


@router.post("/items/{item_id}/batches", status_code=201)
async def create_batch(
    item_id: int,
    data: BatchCreate,
    response: Response,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BatchRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    item = await session.get(Item, item_id)
    if item is None or item.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Item not found")

    location_id = data.location_id
    if location_id is None:
        location_id = await _default_location_id(session, user.household_id)
    if location_id is None:
        raise HTTPException(
            status_code=400,
            detail="No location available — please create a location first",
        )

    location = await session.get(Location, location_id)
    if location is None or location.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Location not found")

    expiry_date = data.expiry_date or date.today() + timedelta(days=365)

    # If a batch already exists for this (item, location, expiry), merge quantities
    # rather than rejecting — user intent is "add stock here", not "create a new record".
    existing = (
        await session.exec(
            select(Batch).where(
                Batch.item_id == item_id,
                Batch.location_id == location_id,
                Batch.expiry_date == expiry_date,
                Batch.household_id == user.household_id,
            )
        )
    ).first()

    if existing is not None:
        existing.quantity += data.quantity
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        response.status_code = 200
        return BatchRead.model_validate(existing)

    batch = Batch(
        item_id=item_id,
        household_id=user.household_id,
        location_id=location_id,
        quantity=data.quantity,
        expiry_date=expiry_date,
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return BatchRead.model_validate(batch)


@router.patch("/batches/{batch_id}")
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BatchRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    batch = await session.get(Batch, batch_id)
    if batch is None or batch.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    updates = data.model_dump(exclude_unset=True)

    if "location_id" in updates and updates["location_id"] is not None:
        location = await session.get(Location, updates["location_id"])
        if location is None or location.household_id != user.household_id:
            raise HTTPException(status_code=404, detail="Location not found")

    # Resolve what the new (location, expiry) would be after the update, then check
    # for a collision BEFORE modifying the batch. Modifying first would mark the ORM
    # object dirty; SQLAlchemy's autoflush would then emit the UPDATE before our SELECT,
    # hitting the unique constraint instead of letting us handle the merge gracefully.
    new_location_id = updates.get("location_id", batch.location_id)
    new_expiry_date = updates.get("expiry_date", batch.expiry_date)

    existing = (
        await session.exec(
            select(Batch).where(
                Batch.item_id == batch.item_id,
                Batch.location_id == new_location_id,
                Batch.expiry_date == new_expiry_date,
                Batch.household_id == user.household_id,
                Batch.id != batch_id,
            )
        )
    ).first()

    if existing is not None:
        existing.quantity += batch.quantity
        session.add(existing)
        await session.delete(batch)
        await session.commit()
        await session.refresh(existing)
        return BatchRead.model_validate(existing)

    for field, value in updates.items():
        setattr(batch, field, value)

    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return BatchRead.model_validate(batch)


@router.delete("/batches/{batch_id}", status_code=204)
async def delete_batch(
    batch_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    batch = await session.get(Batch, batch_id)
    if batch is None or batch.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Batch not found")
    await session.delete(batch)
    await session.commit()


@router.post("/batches/{batch_id}/adjust")
async def adjust_batch(
    batch_id: int,
    data: BatchAdjust,
    response: Response,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BatchRead | None:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    batch = await session.get(Batch, batch_id)
    if batch is None or batch.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    new_quantity = batch.quantity + data.delta

    if new_quantity < 0:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot remove {abs(data.delta)} — only {batch.quantity} in stock",
        )

    if new_quantity == 0:
        # Quantity exhausted — delete the batch rather than storing a zero value.
        await session.delete(batch)
        await session.commit()
        response.status_code = 204
        return None

    batch.quantity = new_quantity
    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return BatchRead.model_validate(batch)


@router.get("/expiring")
async def get_expiring(
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    days: Annotated[int, Query(ge=1)] = 30,
) -> list[BatchRead]:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    cutoff = date.today() + timedelta(days=days)
    result = await session.exec(
        select(Batch)
        .where(
            Batch.household_id == user.household_id,
            Batch.expiry_date <= cutoff,
        )
        .order_by(col(Batch.expiry_date))
    )
    return [BatchRead.model_validate(b) for b in result.all()]
