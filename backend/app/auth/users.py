import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.db import BaseUserDatabase
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.backend import auth_backend
from app.config import get_settings
from app.database import get_session
from app.models.category import Category
from app.models.household import Household
from app.models.location import Location
from app.models.user import User


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[BaseUserDatabase[User, uuid.UUID]]:
    # Imported directly from its package, not via fastapi_users.db, because
    # the re-export there uses try/except which Pylance can't statically trace.
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = get_settings().secret_key.get_secret_value()
    verification_token_secret = get_settings().secret_key.get_secret_value()

    def __init__(
        self,
        user_db: BaseUserDatabase[User, uuid.UUID],
        session: AsyncSession,
    ) -> None:
        super().__init__(user_db)
        self.session = session

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        # FastAPI Users commits the user row before calling this hook, so true
        # atomicity isn't possible. We use a compensating transaction: if
        # household creation fails for any reason, we delete the orphaned user
        # so the DB is left in a consistent state.
        try:
            prefix = user.email.split("@", 1)[0].strip() or "User"
            household = Household(name=f"{prefix}'s household")
            self.session.add(household)
            await self.session.flush()  # writes household row and populates household.id
            # flush always populates the PK; the None check is for type narrowing only.
            if household.id is None:
                raise RuntimeError("Household PK not populated after flush")
            user.household_id = household.id  # session tracks this change automatically
            self.session.add(Location(household_id=household.id, name="Pantry"))
            self.session.add(Category(household_id=household.id, name="Food"))
            await self.session.commit()
        except Exception:
            await self.user_db.delete(user)
            raise


async def get_user_manager(
    user_db: Annotated[BaseUserDatabase[User, uuid.UUID], Depends(get_user_db)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[UserManager]:
    # FastAPI caches dependencies per request, so session here is the same
    # instance already open for get_user_db — no extra connection is opened.
    yield UserManager(user_db, session)


fastapi_users: FastAPIUsers[User, uuid.UUID] = FastAPIUsers(
    get_user_manager,
    [auth_backend],
)

# Import this dependency in any route that requires authentication.
current_active_user = fastapi_users.current_user(active=True)
