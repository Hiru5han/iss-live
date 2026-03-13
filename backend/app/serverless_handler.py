"""AWS Lambda handler that reuses the FastAPI normalization logic."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from .config import Settings
from .crew_client import CrewClient, CrewUnavailableError
from .iss_client import ISSClient, UpstreamUnavailableError
from .iss_track_client import ISSTrackClient, TLEUnavailableError

settings = Settings()
iss_client = ISSClient(
    upstream_url=settings.upstream_url,
    cache_ttl=settings.cache_ttl,
    rate_limit_seconds=settings.rate_limit_seconds,
    timeout=settings.request_timeout,
)
crew_client = CrewClient(
    crew_url=settings.crew_url,
    cache_ttl=settings.crew_cache_ttl,
    timeout=settings.request_timeout,
)
track_client = ISSTrackClient(
    tle_url=settings.tle_url,
    timeout=settings.request_timeout,
)


async def _handle_iss_now() -> dict[str, Any]:
    try:
        payload = await iss_client.fetch()
        body = payload.model_dump()
        status = 200
    except UpstreamUnavailableError as exc:
        body = {"error": str(exc)}
        status = 503

    headers = {
        "Cache-Control": f"max-age={settings.cache_ttl}",
        "Access-Control-Allow-Origin": "*",
    }
    return {"statusCode": status, "body": json.dumps(body), "headers": headers}


async def _handle_crew() -> dict[str, Any]:
    try:
        payload = await crew_client.fetch()
        body = payload.model_dump()
        status = 200
    except CrewUnavailableError as exc:
        body = {"error": str(exc)}
        status = 503

    headers = {
        "Cache-Control": f"max-age={settings.crew_cache_ttl}",
        "Access-Control-Allow-Origin": "*",
    }
    return {"statusCode": status, "body": json.dumps(body), "headers": headers}


async def _handle_history(hours: float) -> dict[str, Any]:
    hours = max(0.25, min(24.0, hours))
    try:
        points = await track_client.get_track(hours)
        body = {"hours": hours, "points": [p.model_dump() for p in points]}
        status = 200
    except TLEUnavailableError as exc:
        body = {"error": str(exc)}
        status = 503

    headers = {
        "Cache-Control": "max-age=60",
        "Access-Control-Allow-Origin": "*",
    }
    return {"statusCode": status, "body": json.dumps(body), "headers": headers}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # pragma: no cover
    path: str = event.get("path", "") or event.get("rawPath", "")
    clean = path.rstrip("/")
    if clean.endswith("/iss/crew"):
        return asyncio.run(_handle_crew())
    if clean.endswith("/iss/history"):
        params = event.get("queryStringParameters") or {}
        try:
            hours = float(params.get("hours", 1.0))
        except (TypeError, ValueError):
            hours = 1.0
        return asyncio.run(_handle_history(hours))
    return asyncio.run(_handle_iss_now())
