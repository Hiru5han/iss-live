"""Pydantic models for ISS backend responses."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    ok: bool = True


class ISSTrackPoint(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")


class ISSTrackResponse(BaseModel):
    hours: float = Field(..., description="Requested history window in hours")
    points: list[ISSTrackPoint] = Field(..., description="Track points sampled every minute")


class CrewMember(BaseModel):
    name: str = Field(..., description="Astronaut name")
    craft: str = Field(default="ISS", description="Spacecraft name")


class CrewResponse(BaseModel):
    count: int = Field(..., description="Number of crew members aboard the ISS")
    members: list[CrewMember] = Field(..., description="List of crew members")


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
