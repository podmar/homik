from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.config import get_settings

# tokenUrl is shown in OpenAPI's "Authorize" dialog — it must match the login route prefix.
_transport = BearerTransport(tokenUrl="auth/jwt/login")


def _get_jwt_strategy() -> JWTStrategy:  # type: ignore[type-arg]
    return JWTStrategy(
        secret=get_settings().secret_key.get_secret_value(),
        # 1-hour token lifetime; increase if UX warrants it
        lifetime_seconds=3600,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=_transport,
    get_strategy=_get_jwt_strategy,
)
