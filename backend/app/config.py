from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    # no default value for database_url, it must be provided via environment variable or .env file
    database_url: SecretStr = Field(
        description="Database URL in the format: postgresql://user:password@host:port/database",
    )
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    # database_url does not have a default value, so if it's missing from the environment variables or .env file,
    # Pydantic will raise a validation error here, which is desirable to catch configuration issues
    # The type ignore below is for static type checkers (e.g., mypy) because 'database_url' has no default value,
    # but this is safe since Pydantic will enforce its presence at runtime.
    return Settings()  # type: ignore[call-arg]
