import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.db import BaseUserDatabase
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.backend import auth_backend
from app.config import get_settings
from app.database import get_session
from app.models.user import User


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[BaseUserDatabase[User, uuid.UUID]]:
    # Imported directly from its package, not via fastapi_users.db, because
    # the re-export there uses try/except which Pylance can't statically trace.
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    # These secrets sign password-reset and verification tokens.
    # Changing them invalidates all outstanding tokens.
    reset_password_token_secret = get_settings().secret_key.get_secret_value()
    verification_token_secret = get_settings().secret_key.get_secret_value()


async def get_user_manager(
    user_db: Annotated[BaseUserDatabase[User, uuid.UUID], Depends(get_user_db)],
) -> AsyncGenerator[UserManager]:
    yield UserManager(user_db)


fastapi_users: FastAPIUsers[User, uuid.UUID] = FastAPIUsers(
    get_user_manager,
    [auth_backend],
)

# Import this dependency in any route that requires authentication.
current_active_user = fastapi_users.current_user(active=True)
