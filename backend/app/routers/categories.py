from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.users import current_active_user
from app.database import get_session
from app.models.category import Category
from app.models.item import Item
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryRead(SQLModel):
    id: int
    name: str


class CategoryCreate(SQLModel):
    name: str = Field(max_length=100)


class CategoryUpdate(SQLModel):
    name: str = Field(max_length=100)


@router.get("")
async def list_categories(
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CategoryRead]:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    result = await session.exec(
        select(Category).where(Category.household_id == user.household_id)
    )
    return [CategoryRead.model_validate(cat) for cat in result.all()]


@router.post("", status_code=201)
async def create_category(
    data: CategoryCreate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    category = Category(household_id=user.household_id, name=data.name)
    session.add(category)
    try:
        await session.commit()
    except IntegrityError:
        # Let the DB enforce the unique constraint on (household_id, name) rather than
        # doing a pre-check query. The broad IntegrityError catch is intentional — inspecting
        # the underlying driver exception (e.g. asyncpg's UniqueViolationError) is fragile
        # across SQLAlchemy versions. In practice, FK and NOT NULL violations are ruled out
        # here: household_id is server-set and name is validated by Pydantic before commit.
        await session.rollback()
        raise HTTPException(status_code=409, detail="Integrity error: a category with this name may already exist in this household") from None
    await session.refresh(category)
    return CategoryRead.model_validate(category)


@router.patch("/{category_id}")
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryRead:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    category = await session.get(Category, category_id)
    if category is None or category.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Category not found")
    category.name = data.name
    session.add(category)
    try:
        await session.commit()
    except IntegrityError:
        # Same reasoning as create_category — unique constraint on (household_id, name).
        await session.rollback()
        raise HTTPException(status_code=409, detail="Integrity error: a category with this name may already exist in this household") from None
    await session.refresh(category)
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    if user.household_id is None:
        raise HTTPException(status_code=400, detail="No household assigned to this account")
    category = await session.get(Category, category_id)
    if category is None or category.household_id != user.household_id:
        raise HTTPException(status_code=404, detail="Category not found")
    # Prevent deleting a category that has items — would silently uncategorise inventory.
    in_use = (
        await session.exec(select(Item.id).where(Item.category_id == category_id).limit(1))
    ).first()
    if in_use is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a category that has items",
        )
    await session.delete(category)
    await session.commit()
