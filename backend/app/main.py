"""FastAPI entrypoint for the ISS Live backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Response
from fastapi.responses import JSONResponse

from .config import Settings
from .iss_client import ISSClient, UpstreamUnavailableError
from .models import HealthResponse, ISSNowResponse

app = FastAPI(title="ISS Live API", version="0.1.0")


def get_settings() -> Settings:
    settings: Settings | None = getattr(app.state, "settings", None)  # type: ignore[attr-defined]
    if settings is None:
        settings = Settings()
        app.state.settings = settings  # type: ignore[attr-defined]
    return settings


def get_iss_client(settings: Annotated[Settings, Depends(get_settings)]) -> ISSClient:
    client: ISSClient | None = getattr(app.state, "iss_client", None)  # type: ignore[attr-defined]
    if client is None:
        client = ISSClient(
            upstream_url=settings.upstream_url,
            cache_ttl=settings.cache_ttl,
            rate_limit_seconds=settings.rate_limit_seconds,
            timeout=settings.request_timeout,
        )
        app.state.iss_client = client  # type: ignore[attr-defined]
    return client


@app.on_event("startup")
async def startup_event() -> None:
    settings = Settings()
    app.state.settings = settings
    app.state.iss_client = ISSClient(
        upstream_url=settings.upstream_url,
        cache_ttl=settings.cache_ttl,
        rate_limit_seconds=settings.rate_limit_seconds,
        timeout=settings.request_timeout,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    iss_client: ISSClient | None = getattr(app.state, "iss_client", None)
    if iss_client:
        await iss_client.aclose()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True)


@app.get("/iss/now", response_model=ISSNowResponse)
async def iss_now(
    response: Response, iss_client: Annotated[ISSClient, Depends(get_iss_client)]
) -> ISSNowResponse | JSONResponse:
    try:
        payload = await iss_client.fetch()
    except UpstreamUnavailableError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc)},
            headers={
                "Cache-Control": f"max-age={iss_client.cache_ttl}",
                "Access-Control-Allow-Origin": "*",
            },
        )

    response.headers["Cache-Control"] = f"max-age={iss_client.cache_ttl}"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return payload
