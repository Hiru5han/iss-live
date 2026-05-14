from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.iss_track_client import ISSTrackClient, TLEUnavailableError
from app.main import app, get_track_client


def _mock_track_client(
    lat: float = 10.0,
    lon: float = 20.0,
    alt: float = 420.0,
    velocity: float = 27600.0,
) -> AsyncMock:
    client = AsyncMock(spec=ISSTrackClient)
    client.get_position_now.return_value = (lat, lon, alt, velocity)
    return client


def test_iss_now_returns_tlesourced_payload() -> None:
    app.dependency_overrides[get_track_client] = lambda: _mock_track_client()

    with TestClient(app) as client:
        response = client.get("/iss/now")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["lat"] == 10.0
    assert data["lon"] == 20.0
    assert data["altitude_km"] == 420.0
    assert data["velocity_kmh"] == 27600.0
    assert data["source"] == "tle/sgp4"
    assert data["stale"] is False
    assert "timestamp" in data


def test_iss_now_returns_503_when_tle_unavailable() -> None:
    mock_client = AsyncMock(spec=ISSTrackClient)
    mock_client.get_position_now.side_effect = TLEUnavailableError("TLE fetch failed")
    app.dependency_overrides[get_track_client] = lambda: mock_client

    with TestClient(app) as client:
        response = client.get("/iss/now")

    app.dependency_overrides.clear()

    assert response.status_code == 503
