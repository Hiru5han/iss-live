"""AWS Lambda handler that reuses the FastAPI normalization logic."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from .config import Settings
from .crew_client import CrewClient, CrewUnavailableError
from .iss_client import ISSClient, UpstreamUnavailableError

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


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # pragma: no cover
    path: str = event.get("path", "") or event.get("rawPath", "")
    if path.rstrip("/").endswith("/iss/crew"):
        return asyncio.run(_handle_crew())
    return asyncio.run(_handle_iss_now())
