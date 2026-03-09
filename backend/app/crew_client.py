"""Client to fetch current ISS crew from open-notify.org."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .models import CrewMember, CrewResponse


class CrewUnavailableError(Exception):
    """Raised when the crew API cannot be reached and no cache is available."""


@dataclass
class CrewCacheEntry:
    payload: CrewResponse
    stored_at: float


class CrewClient:
    """Fetches ISS crew data with caching."""

    def __init__(
        self,
        crew_url: str,
        *,
        cache_ttl: int,
        timeout: float,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.crew_url = crew_url
        self.cache_ttl = cache_ttl
        self._cache: Optional[CrewCacheEntry] = None
        self._client = httpx.AsyncClient(timeout=timeout, transport=transport)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self) -> CrewResponse:
        now = time.monotonic()
        cached = self._cache
        if cached and (now - cached.stored_at) < self.cache_ttl:
            return cached.payload

        try:
            response = await self._client.get(self.crew_url)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except httpx.HTTPError as exc:
            if cached:
                return cached.payload
            raise CrewUnavailableError("Crew data unavailable") from exc

        members = [
            CrewMember(name=p["name"], craft=p["craft"])
            for p in data.get("people", [])
            if p.get("craft") == "ISS"
        ]
        result = CrewResponse(count=len(members), members=members)
        self._cache = CrewCacheEntry(payload=result, stored_at=now)
        return result
