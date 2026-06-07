from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.users import current_active_user
from app.database import get_session
from app.models.batch import Batch
from app.models.location import Location
from app.models.user import User

router = APIRouter(prefix="/locations", tags=["locations"])


class LocationRead(SQLModel):
    id: int
    name: str


class LocationCreate(SQLModel):
    name: str = Field(max_length=100)


class LocationUpdate(SQLModel):
    name: str = Field(max_length=100)


@router.get("")
async def list_locations(
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[LocationRead]:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    result = await session.exec(
        select(Location).where(Location.household_id == user.household_id)
    )
    return [LocationRead.model_validate(loc) for loc in result.all()]


@router.post("", status_code=201)
async def create_location(
    data: LocationCreate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LocationRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    location = Location(household_id=user.household_id, name=data.name)
    session.add(location)
    try:
        await session.commit()
    except IntegrityError:
        # Let the DB enforce the unique constraint on (household_id, name) rather than
        # doing a pre-check query. The broad IntegrityError catch is intentional — inspecting
        # the underlying driver exception (e.g. asyncpg's UniqueViolationError) is fragile
        # across SQLAlchemy versions. In practice, FK and NOT NULL violations are ruled out
        # here: household_id is server-set and name is validated by Pydantic before commit.
        await session.rollback()
        raise HTTPException(status_code=409, detail="Integrity error: a location with this name may already exist in this household") from None
    await session.refresh(location)
    return LocationRead.model_validate(location)


@router.patch("/{location_id}")
async def update_location(
    location_id: int,
    data: LocationUpdate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LocationRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    location = await session.get(Location, location_id)
    if location is None or location.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Location not found")
    location.name = data.name
    session.add(location)
    try:
        await session.commit()
    except IntegrityError:
        # Same reasoning as create_location — unique constraint on (household_id, name).
        await session.rollback()
        raise HTTPException(status_code=409, detail="Integrity error: a location with this name may already exist in this household") from None
    await session.refresh(location)
    return LocationRead.model_validate(location)


@router.delete("/{location_id}", status_code=204)
async def delete_location(
    location_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    location = await session.get(Location, location_id)
    if location is None or location.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Location not found")
    # Prevent deleting a location that has batches — would orphan inventory data.
    in_use = (
        await session.exec(select(Batch.id).where(Batch.location_id == location_id).limit(1))
    ).first()
    if in_use is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a location that has batches",
        )
    await session.delete(location)
    await session.commit()
