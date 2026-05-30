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
    return Settings()  # type: ignore[call-arg]
