"""
Centralized application configuration.

All environment-dependent values are loaded here and nowhere else.
No other module should call os.environ / os.getenv directly -- this
is the single source of truth for config, which makes secrets easy
to audit and rotate.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRETS = {
    "changeme", "secret", "your-secret-key", "test",
    "replace-with-output-of-secrets.token_urlsafe-64",
}


class Settings(BaseSettings):
    # -- App metadata --------------------------------------------------
    APP_NAME: str = "Custom Analytics Backend"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # -- Security / JWT --------------------------------------------------
    # No default for the secret key -- the app must refuse to start
    # rather than silently run with a guessable key.
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # -- Database --------------------------------------------------
    # Optional at boot time on purpose: early development phase
    # runs entirely on mock repositories, per the layered-build plan.
    DATABASE_URL: PostgresDsn | None = None
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 10
    DB_CONNECT_TIMEOUT_SECONDS: int = 5

    # -- Redis (caching, rate limiting, JWT revocation) --------------------------------------------------
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_POOL_MAX_CONNECTIONS: int = 20
    REDIS_CONNECT_TIMEOUT_SECONDS: int = 5
    CACHE_DEFAULT_TTL_SECONDS: int = 60

    # -- CORS --------------------------------------------------
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    # -- Rate limiting (Redis-backed) --------------------------------------------------
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5

    # -- App database (SQLite -- user accounts, separate from Postgres/rudder_schema) ----
    SQLITE_DB_PATH: str = "app_data.db"

    # -- Bootstrap superadmin --------------------------------------------------
    # No defaults -- the app must refuse to start rather than silently
    # boot with a guessable superadmin account, same principle as
    # JWT_SECRET_KEY above.
    SUPERADMIN_USERNAME: str = Field(..., min_length=3, max_length=50)
    SUPERADMIN_PASSWORD: str = Field(..., min_length=8, max_length=128)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",  # unknown env vars fail loudly instead of being silently ignored
    )

    @field_validator("JWT_SECRET_KEY", "SUPERADMIN_PASSWORD")
    @classmethod
    def _reject_weak_secret(cls, v: str) -> str:
        if v.lower() in _PLACEHOLDER_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY is set to a placeholder value. "
                "Generate a real secret, e.g.: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.

    Using a function (rather than a module-level singleton constructed
    at import time) makes this trivially mockable in tests via
    get_settings.cache_clear() + dependency override.
    """
    return Settings()   