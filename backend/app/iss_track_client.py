"""Client for computing ISS historical track using TLE propagation."""

from __future__ import annotations

import asyncio
import math
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sgp4.api import Satrec, jday

from .models import ISSTrackPoint

TLE_CACHE_TTL = 3600  # refresh TLE at most once per hour


class TLEUnavailableError(Exception):
    """Raised when TLE data cannot be fetched and no cached copy is available."""


class ISSTrackClient:
    """Fetches the ISS TLE and propagates historical positions via SGP4."""

    def __init__(
        self,
        tle_url: str,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.tle_url = tle_url
        self._lock = asyncio.Lock()
        self._tle_cache: tuple[str, str] | None = None  # (line1, line2)
        self._tle_cached_at: float = 0.0
        self._client = httpx.AsyncClient(timeout=timeout, transport=transport)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_position_now(self) -> tuple[float, float, float, float]:
        """Return (lat_deg, lon_deg, alt_km, velocity_kmh) for the current moment."""
        line1, line2 = await self._get_tle()
        sat = Satrec.twoline2rv(line1, line2)
        now = datetime.now(UTC)
        jd_day, jd_fr = _jday_from_datetime(now)
        error_code, r, v = sat.sgp4(jd_day, jd_fr)
        if error_code != 0:
            raise TLEUnavailableError(f"SGP4 propagation error {error_code}")
        lat, lon, alt = _teme_to_geodetic(r, jd_day + jd_fr)
        velocity_kmh = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) * 3600.0
        return round(lat, 4), round(lon, 4), round(alt, 2), round(velocity_kmh, 2)

    async def get_track(self, hours: float) -> list[ISSTrackPoint]:
        """Return positions sampled every minute for the past *hours* hours."""
        line1, line2 = await self._get_tle()
        sat = Satrec.twoline2rv(line1, line2)

        now = datetime.now(UTC)
        start = now - timedelta(hours=hours)

        points: list[ISSTrackPoint] = []
        t = start
        while t <= now:
            jd_day, jd_fr = _jday_from_datetime(t)
            error_code, r, _ = sat.sgp4(jd_day, jd_fr)
            if error_code == 0:
                lat, lon, _ = _teme_to_geodetic(r, jd_day + jd_fr)
                points.append(
                    ISSTrackPoint(
                        lat=round(lat, 4),
                        lon=round(lon, 4),
                        timestamp=t.isoformat().replace("+00:00", "Z"),
                    )
                )
            t += timedelta(minutes=1)

        return points

    async def _get_tle(self) -> tuple[str, str]:
        async with self._lock:
            now = time.monotonic()
            if self._tle_cache and (now - self._tle_cached_at) < TLE_CACHE_TTL:
                return self._tle_cache

            try:
                response = await self._client.get(self.tle_url)
                response.raise_for_status()
                self._tle_cache = _parse_tle(response.text)
                self._tle_cached_at = now
                return self._tle_cache
            except (httpx.HTTPError, ValueError) as exc:
                if self._tle_cache:
                    return self._tle_cache
                raise TLEUnavailableError("Cannot fetch ISS TLE data") from exc


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_tle(text: str) -> tuple[str, str]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError(f"Too few TLE lines: {lines!r}")
    # Accept both 2-line and 3-line (name + two lines) formats
    return lines[-2], lines[-1]


def _jday_from_datetime(dt: datetime) -> tuple[float, float]:
    return jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)


def _gmst(jd_full: float) -> float:
    """Greenwich Mean Sidereal Time in radians."""
    t = (jd_full - 2451545.0) / 36525.0
    deg = (
        280.46061837
        + 360.98564736629 * (jd_full - 2451545.0)
        + 0.000387933 * t * t
        - t * t * t / 38710000.0
    )
    return math.radians(deg % 360.0)


def _teme_to_geodetic(r_teme: Any, jd: float) -> tuple[float, float, float]:
    """Convert a TEME position vector (km) to geodetic (lat°, lon°, alt km)."""
    g = _gmst(jd)
    cos_g, sin_g = math.cos(g), math.sin(g)

    # TEME → ECEF rotation about Z-axis by GMST
    x = r_teme[0] * cos_g + r_teme[1] * sin_g
    y = -r_teme[0] * sin_g + r_teme[1] * cos_g
    z = r_teme[2]

    # WGS-84 constants
    a = 6378.137  # equatorial radius, km
    f = 1.0 / 298.257223563
    e2 = 2.0 * f - f * f

    p = math.sqrt(x * x + y * y)
    lon = math.atan2(y, x)

    # Iterative geodetic latitude (Bowring / Vermeille)
    lat = math.atan2(z, p)
    for _ in range(5):
        sin_lat = math.sin(lat)
        n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        lat = math.atan2(z + e2 * n * sin_lat, p)

    sin_lat = math.sin(lat)
    n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - n

    return math.degrees(lat), math.degrees(lon), alt
