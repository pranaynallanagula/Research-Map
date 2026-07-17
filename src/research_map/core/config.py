from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://research_map:research_map@localhost:5432/research_map"
    )
    redis_url: str = "redis://localhost:6379/0"
    ai_api_key: SecretStr | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the shared application settings instance."""

    return Settings()
