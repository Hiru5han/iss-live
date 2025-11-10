"""AWS Lambda handler that reuses the FastAPI normalization logic."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from .config import Settings
from .iss_client import ISSClient, UpstreamUnavailableError

settings = Settings()
client = ISSClient(
    upstream_url=settings.upstream_url,
    cache_ttl=settings.cache_ttl,
    rate_limit_seconds=settings.rate_limit_seconds,
    timeout=settings.request_timeout,
)


async def _handle_request() -> Dict[str, Any]:
    try:
        payload = await client.fetch()
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


def handler(event: dict[str, Any], context: Any) -> Dict[str, Any]:  # pragma: no cover - Lambda entry
    return asyncio.run(_handle_request())
