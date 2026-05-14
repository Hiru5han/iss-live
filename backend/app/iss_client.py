"""Client helpers to fetch and cache ISS position data."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

from .models import ISSNowResponse

if TYPE_CHECKING:
    from .iss_track_client import ISSTrackClient


class UpstreamUnavailableError(Exception):
    """Raised when the upstream API cannot be reached and no cache is available."""


@dataclass
class CacheEntry:
    payload: ISSNowResponse
    stored_at: float


class ISSClient:
    """Fetches ISS data with caching, rate limiting, and graceful fallback."""

    def __init__(
        self,
        upstream_url: str,
        *,
        cache_ttl: int,
        rate_limit_seconds: int,
        timeout: float,
        source: str = "wheretheiss.at",
        transport: httpx.BaseTransport | None = None,
        track_client: ISSTrackClient | None = None,
    ) -> None:
        self.upstream_url = upstream_url
        self.cache_ttl = cache_ttl
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout = timeout
        self.source = source
        self._lock = asyncio.Lock()
        self._cache: CacheEntry | None = None
        self._next_allowed_fetch = 0.0
        self._client = httpx.AsyncClient(timeout=self.timeout, transport=transport)
        self._track_client = track_client

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self) -> ISSNowResponse:
        async with self._lock:
            now = time.monotonic()
            cached = self._cache
            if cached and (now - cached.stored_at) < self.cache_ttl:
                return cached.payload

            if cached and now < self._next_allowed_fetch:
                return cached.payload

            try:
                payload = await self._fetch_upstream()
            except (httpx.HTTPError, ValueError) as exc:
                if cached:
                    cached_payload = cached.payload.model_copy(deep=True)
                    cached_payload.stale = True
                    return cached_payload
                if self._track_client is not None:
                    try:
                        return await self._fetch_via_tle()
                    except Exception:  # noqa: S110
                        pass
                raise UpstreamUnavailableError("Upstream ISS provider unavailable") from exc

            result = self._normalize_payload(payload)
            self._cache = CacheEntry(payload=result, stored_at=now)
            self._next_allowed_fetch = now + self.rate_limit_seconds
            return result

    async def _fetch_via_tle(self) -> ISSNowResponse:
        lat, lon, alt, velocity = await self._track_client.get_position_now()  # type: ignore[union-attr]
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return ISSNowResponse(
            lat=lat,
            lon=lon,
            altitude_km=alt,
            velocity_kmh=velocity,
            timestamp=ts,
            source="tle/sgp4",
            stale=False,
        )

    async def _fetch_upstream(self) -> dict[str, Any]:
        response = await self._client.get(self.upstream_url)
        response.raise_for_status()
        return response.json()

    def _normalize_payload(self, payload: dict[str, Any]) -> ISSNowResponse:
        timestamp = datetime.fromtimestamp(payload["timestamp"], tz=UTC)
        return ISSNowResponse(
            lat=payload["latitude"],
            lon=payload["longitude"],
            altitude_km=payload["altitude"],
            velocity_kmh=payload["velocity"],
            timestamp=timestamp,
            source=self.source,
            stale=False,
        )
