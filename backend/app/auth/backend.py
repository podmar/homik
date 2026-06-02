import uuid

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.config import get_settings
from app.models.user import User

# tokenUrl is shown in OpenAPI's "Authorize" dialog — it must match the login route prefix.
_transport = BearerTransport(tokenUrl="auth/jwt/login")


def _get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    settings = get_settings()
    return JWTStrategy(
        secret=settings.secret_key.get_secret_value(),
        # 1-hour token lifetime; increase if UX warrants it
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        algorithm=settings.algorithm,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=_transport,
    get_strategy=_get_jwt_strategy,
)
