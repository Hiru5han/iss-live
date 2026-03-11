"""Client helpers to fetch and cache ISS position data."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from .models import ISSNowResponse


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
                raise UpstreamUnavailableError("Upstream ISS provider unavailable") from exc

            result = self._normalize_payload(payload)
            self._cache = CacheEntry(payload=result, stored_at=now)
            self._next_allowed_fetch = now + self.rate_limit_seconds
            return result

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
