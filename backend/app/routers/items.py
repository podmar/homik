from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Field, SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.users import current_active_user
from app.database import get_session
from app.models.batch import Batch
from app.models.category import Category
from app.models.item import Item
from app.models.user import User

router = APIRouter(prefix="/items", tags=["items"])


class ItemRead(SQLModel):
    id: int
    name: str
    barcode: str | None
    brand: str | None
    image_url: str | None
    category_id: int | None
    unit: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ItemCreate(SQLModel):
    name: str = Field(max_length=200)
    barcode: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=200)
    image_url: str | None = Field(default=None, max_length=500)
    category_id: int | None = None
    unit: str = Field(max_length=50)
    notes: str | None = Field(default=None, max_length=1000)


class ItemUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=200)
    barcode: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=200)
    image_url: str | None = Field(default=None, max_length=500)
    category_id: int | None = None
    unit: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)


@router.get("")
async def list_items(
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    name: str | None = None,
    location_id: int | None = None,
) -> list[ItemRead]:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    query = select(Item).where(Item.household_id == user.household_id)
    if name is not None:
        # col() wraps the model attribute as a SQLAlchemy column expression so
        # Pyright knows .ilike() is a SQL method, not a str method.
        query = query.where(col(Item.name).ilike(f"%{name}%"))
    if location_id is not None:
        matched = select(Batch.item_id).where(
            Batch.location_id == location_id,
            Batch.household_id == user.household_id,
        )
        query = query.where(col(Item.id).in_(matched))
    result = await session.exec(query.order_by(Item.name))
    return [ItemRead.model_validate(item) for item in result.all()]


@router.get("/{item_id}")
async def get_item(
    item_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    item = await session.get(Item, item_id)
    if item is None or item.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemRead.model_validate(item)


@router.post("", status_code=201)
async def create_item(
    data: ItemCreate,
    response: Response,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    # If a barcode is provided and already exists in this household, return the existing
    # item (200) so the client can proceed to add a new Batch against it.
    if data.barcode is not None:
        existing = (
            await session.exec(
                select(Item).where(
                    Item.household_id == user.household_id,
                    Item.barcode == data.barcode,
                )
            )
        ).first()
        if existing is not None:
            response.status_code = 200
            return ItemRead.model_validate(existing)

    if data.category_id is not None:
        category = await session.get(Category, data.category_id)
        if category is None or category.household_id != user.household_id:
            raise HTTPException(status_code=404, detail="Category not found")

    item = Item(household_id=user.household_id, **data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return ItemRead.model_validate(item)


@router.patch("/{item_id}")
async def update_item(
    item_id: int,
    data: ItemUpdate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    item = await session.get(Item, item_id)
    if item is None or item.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = data.model_dump(exclude_unset=True)

    if "category_id" in updates and updates["category_id"] is not None:
        category = await session.get(Category, updates["category_id"])
        if category is None or category.household_id != user.household_id:
            raise HTTPException(status_code=404, detail="Category not found")

    for field, value in updates.items():
        setattr(item, field, value)

    session.add(item)
    await session.commit()
    await session.refresh(item)
    return ItemRead.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    item = await session.get(Item, item_id)
    if item is None or item.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Item not found")
    # Cascade: remove all batches before deleting the item to respect the FK constraint.
    batches = (await session.exec(select(Batch).where(Batch.item_id == item_id))).all()
    for batch in batches:
        await session.delete(batch)
    await session.delete(item)
    await session.commit()
