"""Tests for the /iss/history endpoint."""

import asyncio

import httpx
from fastapi.testclient import TestClient

from app.iss_track_client import ISSTrackClient
from app.main import app, get_track_client

# Minimal valid TLE for the ISS
_TLE = (
    "ISS (ZARYA)\n"
    "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9025\n"
    "2 25544  51.6400 208.9163 0006941  86.2513 273.9367 15.49829509433882\n"
)


def _make_track_client() -> ISSTrackClient:
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, text=_TLE))
    return ISSTrackClient(tle_url="https://example.com", timeout=1.0, transport=transport)


def test_iss_history_returns_points() -> None:
    client = _make_track_client()
    app.dependency_overrides[get_track_client] = lambda: client

    with TestClient(app) as tc:
        response = tc.get("/iss/history?hours=0.25")

    app.dependency_overrides.clear()
    asyncio.run(client.aclose())

    assert response.status_code == 200
    data = response.json()
    assert data["hours"] == 0.25
    # 0.25 h = 15 min → 16 points (t=0,1,...,15)
    assert len(data["points"]) == 16
    first = data["points"][0]
    assert "lat" in first and "lon" in first and "timestamp" in first
    assert -90 <= first["lat"] <= 90
    assert -180 <= first["lon"] <= 180


def test_iss_history_clamps_hours() -> None:
    """hours is clamped to [0.25, 24.0] server-side."""
    client = _make_track_client()
    app.dependency_overrides[get_track_client] = lambda: client

    with TestClient(app) as tc:
        response = tc.get("/iss/history?hours=0.01")

    app.dependency_overrides.clear()
    asyncio.run(client.aclose())

    assert response.status_code == 200
    data = response.json()
    # clamped to 0.25, so at least 16 points
    assert data["hours"] == 0.25
    assert len(data["points"]) == 16


def test_iss_history_503_on_tle_failure() -> None:
    def _fail(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("unreachable", request=_req)

    transport = httpx.MockTransport(_fail)
    client = ISSTrackClient(tle_url="https://example.com", timeout=1.0, transport=transport)
    app.dependency_overrides[get_track_client] = lambda: client

    with TestClient(app) as tc:
        response = tc.get("/iss/history?hours=1")

    app.dependency_overrides.clear()
    asyncio.run(client.aclose())

    assert response.status_code == 503
    assert "error" in response.json()
