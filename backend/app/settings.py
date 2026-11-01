"""Cached environment configuration, without startup key requirements."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Runtime environment values."""

    gemini_api_key: str | None
    env: str
    log_level: str
    rate_limit_enabled: bool
    serve_frontend: bool = True


@lru_cache
def get_settings() -> Settings:
    """Read settings once per process."""
    env = os.getenv("ENV", "production")
    return Settings(
        os.getenv("GEMINI_API_KEY"),
        env,
        os.getenv("LOG_LEVEL", "INFO"),
        env != "test",
        serve_frontend=os.getenv("SERVE_FRONTEND", "true").lower() == "true",
    )
