import asyncio

import httpx
from fastapi.testclient import TestClient

from app.crew_client import CrewClient
from app.main import app, get_crew_client


def _build_astros_payload() -> dict:
    return {
        "number": 3,
        "people": [
            {"name": "Alice", "craft": "ISS"},
            {"name": "Bob", "craft": "ISS"},
            {"name": "Charlie", "craft": "Tiangong"},
        ],
        "message": "success",
    }


def test_crew_returns_iss_members_only() -> None:
    payload = _build_astros_payload()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    crew_client = CrewClient(
        crew_url="https://example.com",
        cache_ttl=300,
        timeout=0.1,
        transport=transport,
    )

    app.dependency_overrides[get_crew_client] = lambda: crew_client

    with TestClient(app) as client:
        response = client.get("/iss/crew")

    app.dependency_overrides.clear()
    asyncio.run(crew_client.aclose())

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    names = [m["name"] for m in data["members"]]
    assert "Alice" in names
    assert "Bob" in names
    assert "Charlie" not in names


def test_crew_503_when_upstream_down_and_no_cache() -> None:
    transport = httpx.MockTransport(
        lambda request: (_ for _ in ()).throw(httpx.ConnectTimeout("boom", request=request))
    )
    crew_client = CrewClient(
        crew_url="https://example.com",
        cache_ttl=300,
        timeout=0.1,
        transport=transport,
    )

    app.dependency_overrides[get_crew_client] = lambda: crew_client

    with TestClient(app) as client:
        response = client.get("/iss/crew")

    app.dependency_overrides.clear()
    asyncio.run(crew_client.aclose())

    assert response.status_code == 503
    assert "error" in response.json()
