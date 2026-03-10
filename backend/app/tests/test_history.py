import asyncio
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.history_client import HistoryClient
from app.main import app, get_history_client


def _build_positions_response(timestamps: list[int]) -> list[dict]:
    """Build a mock response matching the wheretheiss.at positions endpoint."""
    return [
        {
            "latitude": 10.0 + i,
            "longitude": 20.0 + i,
            "altitude": 420.0,
            "velocity": 27600.0,
            "timestamp": ts,
        }
        for i, ts in enumerate(timestamps)
    ]


def test_history_returns_positions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        ts_param = url.split("timestamps=")[1].split("&")[0]
        timestamps = [int(t) for t in ts_param.split(",")]
        return httpx.Response(200, json=_build_positions_response(timestamps))

    transport = httpx.MockTransport(handler)
    history_client = HistoryClient(
        upstream_base="https://example.com",
        cache_ttl=0,
        timeout=30.0,
        transport=transport,
    )

    app.dependency_overrides[get_history_client] = lambda: history_client

    with TestClient(app) as client:
        response = client.get("/iss/history")

    app.dependency_overrides.clear()
    asyncio.run(history_client.aclose())

    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert "count" in data
    assert data["count"] == len(data["positions"])
    assert data["count"] > 0

    first = data["positions"][0]
    assert "lat" in first
    assert "lon" in first
    assert "timestamp" in first


def test_history_returns_503_on_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=request)

    transport = httpx.MockTransport(handler)
    history_client = HistoryClient(
        upstream_base="https://example.com",
        cache_ttl=0,
        timeout=0.1,
        transport=transport,
    )

    app.dependency_overrides[get_history_client] = lambda: history_client

    with TestClient(app) as client:
        response = client.get("/iss/history")

    app.dependency_overrides.clear()
    asyncio.run(history_client.aclose())

    assert response.status_code == 503


def test_history_serves_cache_on_failure() -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] <= 144:  # First full fetch (1440 timestamps / 10 batch size)
            url = str(request.url)
            ts_param = url.split("timestamps=")[1].split("&")[0]
            timestamps = [int(t) for t in ts_param.split(",")]
            return httpx.Response(200, json=_build_positions_response(timestamps))
        raise httpx.ConnectTimeout("boom", request=request)

    transport = httpx.MockTransport(handler)
    history_client = HistoryClient(
        upstream_base="https://example.com",
        cache_ttl=0,
        timeout=30.0,
        transport=transport,
    )

    app.dependency_overrides[get_history_client] = lambda: history_client

    with TestClient(app) as client:
        first = client.get("/iss/history")
        second = client.get("/iss/history")

    app.dependency_overrides.clear()
    asyncio.run(history_client.aclose())

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["count"] > 0
