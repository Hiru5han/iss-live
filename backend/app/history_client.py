"""Client to fetch 24-hour ISS position history from wheretheiss.at."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from .models import ISSHistoryResponse, ISSPositionRecord

# 24 hours in seconds
HISTORY_WINDOW = 86400

# Sample every 60 seconds → 1440 points for 24 hours
SAMPLE_INTERVAL = 60

# Maximum timestamps per upstream request (API limit)
BATCH_SIZE = 10


class HistoryUnavailableError(Exception):
    """Raised when historical positions cannot be fetched and no cache exists."""


@dataclass
class HistoryCacheEntry:
    payload: ISSHistoryResponse
    stored_at: float


class HistoryClient:
    """Fetches 24-hour ISS position history with caching."""

    def __init__(
        self,
        upstream_base: str = "https://api.wheretheiss.at/v1/satellites/25544",
        *,
        cache_ttl: int = 300,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.upstream_base = upstream_base.rstrip("/")
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._lock = asyncio.Lock()
        self._cache: HistoryCacheEntry | None = None
        self._client = httpx.AsyncClient(timeout=self.timeout, transport=transport)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self) -> ISSHistoryResponse:
        async with self._lock:
            now_mono = time.monotonic()
            cached = self._cache
            if cached and (now_mono - cached.stored_at) < self.cache_ttl:
                return cached.payload

            try:
                positions = await self._fetch_history()
            except (httpx.HTTPError, Exception) as exc:
                if cached:
                    return cached.payload
                raise HistoryUnavailableError(
                    "Unable to fetch ISS history"
                ) from exc

            result = ISSHistoryResponse(
                positions=positions,
                count=len(positions),
            )
            self._cache = HistoryCacheEntry(payload=result, stored_at=now_mono)
            return result

    async def _fetch_history(self) -> list[ISSPositionRecord]:
        now = int(datetime.now(tz=UTC).timestamp())
        start = now - HISTORY_WINDOW

        timestamps = list(range(start, now, SAMPLE_INTERVAL))

        all_positions: list[ISSPositionRecord] = []

        for i in range(0, len(timestamps), BATCH_SIZE):
            batch = timestamps[i : i + BATCH_SIZE]
            ts_param = ",".join(str(t) for t in batch)
            url = f"{self.upstream_base}/positions?timestamps={ts_param}&units=kilometers"
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            for entry in data:
                ts_dt = datetime.fromtimestamp(entry["timestamp"], tz=UTC)
                all_positions.append(
                    ISSPositionRecord(
                        lat=entry["latitude"],
                        lon=entry["longitude"],
                        timestamp=ts_dt,
                    )
                )

        all_positions.sort(key=lambda p: p.timestamp)
        return all_positions
