"""Pydantic models for ISS backend responses."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    ok: bool = True


class CrewMember(BaseModel):
    name: str = Field(..., description="Astronaut name")
    craft: str = Field(default="ISS", description="Spacecraft name")


class CrewResponse(BaseModel):
    count: int = Field(..., description="Number of crew members aboard the ISS")
    members: list[CrewMember] = Field(..., description="List of crew members")


class ISSPositionRecord(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    timestamp: str = Field(..., description="Timestamp in ISO-8601 UTC format")

    @model_validator(mode="before")
    @classmethod
    def ensure_timestamp_str(cls, data: Any) -> Any:
        ts = data.get("timestamp")
        if isinstance(ts, datetime):
            data["timestamp"] = (
                ts.astimezone(UTC).replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
            )
        return data


class ISSHistoryResponse(BaseModel):
    positions: list[ISSPositionRecord] = Field(
        ..., description="Historical positions for the past 24 hours"
    )
    count: int = Field(..., description="Number of position records")


class ISSNowResponse(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    altitude_km: float = Field(..., description="Altitude above mean sea level in km")
    velocity_kmh: float = Field(..., description="Velocity in km/h")
    timestamp: str = Field(..., description="Timestamp in ISO-8601 UTC format")
    source: str = Field(default="wheretheiss.at")
    stale: bool = Field(
        default=False, description="True when cache is served after an upstream failure"
    )

    @model_validator(mode="before")
    @classmethod
    def ensure_timestamp_format(cls, data: Any) -> Any:
        ts = data.get("timestamp")
        if isinstance(ts, datetime):
            data["timestamp"] = (
                ts.astimezone(UTC).replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
            )
        return data
