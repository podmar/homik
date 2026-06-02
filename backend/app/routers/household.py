from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.database import get_session
from app.models.household import Household
from app.models.user import User

router = APIRouter(prefix="/household", tags=["household"])


@router.get("/me")
async def get_my_household(
    user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Household:
    if user.household_id is None:
        raise HTTPException(
            status_code=404, detail="No household assigned to this user"
        )
    household = await session.get(Household, user.household_id)
    if household is None:
        # Shouldn't happen if FKs are enforced, but guards against stale data.
        raise HTTPException(
            status_code=500,
            detail="Household reference is invalid. Please contact support.",
        )
    return household
