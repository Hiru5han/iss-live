import asyncio
from datetime import datetime, timezone

import httpx
from fastapi.testclient import TestClient

from app.iss_client import ISSClient
from app.main import app, get_iss_client


def _build_payload() -> dict[str, float | int]:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return {
        "latitude": 10.0,
        "longitude": 20.0,
        "altitude": 420.0,
        "velocity": 27600.0,
        "timestamp": int(now.timestamp()),
    }


def test_iss_now_returns_normalised_payload() -> None:
    payload = _build_payload()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    iss_client = ISSClient(
        upstream_url="https://example.com",
        cache_ttl=8,
        rate_limit_seconds=0,
        timeout=0.1,
        transport=transport,
    )

    app.dependency_overrides[get_iss_client] = lambda: iss_client

    with TestClient(app) as client:
        response = client.get("/iss/now")

    app.dependency_overrides.clear()
    asyncio.run(iss_client.aclose())

    assert response.status_code == 200
    data = response.json()
    assert data["lat"] == payload["latitude"]
    assert data["lon"] == payload["longitude"]
    assert data["altitude_km"] == payload["altitude"]
    assert data["velocity_kmh"] == payload["velocity"]
    assert data["source"] == "wheretheiss.at"
    assert data["stale"] is False


def test_stale_cache_served_on_upstream_failure() -> None:
    payload = _build_payload()
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(200, json=payload)
        raise httpx.ConnectTimeout("boom", request=request)

    transport = httpx.MockTransport(handler)
    iss_client = ISSClient(
        upstream_url="https://example.com",
        cache_ttl=0,
        rate_limit_seconds=0,
        timeout=0.1,
        transport=transport,
    )

    app.dependency_overrides[get_iss_client] = lambda: iss_client

    with TestClient(app) as client:
        first = client.get("/iss/now")
        second = client.get("/iss/now")

    app.dependency_overrides.clear()
    asyncio.run(iss_client.aclose())

    assert first.status_code == 200
    assert first.json()["stale"] is False

    assert second.status_code == 200
    assert second.json()["stale"] is True
