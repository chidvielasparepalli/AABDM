from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./aabdm.db"

    # Clerk Auth
    clerk_publishable_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Logging
    log_level: str = "INFO"

    # API
    api_version: str = "0.1.0"
    api_title: str = "AABDM API"

    # Run alembic upgrade head on startup (disable in tests)
    auto_migrate: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
