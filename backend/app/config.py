"""Application settings management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    upstream_url: str = Field(default="https://api.wheretheiss.at/v1/satellites/25544")
    cache_ttl: int = Field(default=8)
    rate_limit_seconds: int = Field(default=5)
    request_timeout: float = Field(default=2.0)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", validate_default=True)
