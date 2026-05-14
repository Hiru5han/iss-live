"""Application settings management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    request_timeout: float = Field(default=2.0)
    crew_url: str = Field(default="http://api.open-notify.org/astros.json")
    crew_cache_ttl: int = Field(default=300)
    tle_url: str = Field(default="https://celestrak.org/satcat/tle.php?CATNR=25544")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", validate_default=True
    )
