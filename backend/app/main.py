"""FastAPI entrypoint for the ISS Live backend."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Response
from fastapi.responses import JSONResponse

from .config import Settings
from .crew_client import CrewClient, CrewUnavailableError
from .iss_track_client import ISSTrackClient, TLEUnavailableError
from .models import CrewResponse, HealthResponse, ISSNowResponse, ISSTrackResponse

app = FastAPI(title="ISS Live API", version="0.1.0")


def get_settings() -> Settings:
    settings: Settings | None = getattr(app.state, "settings", None)  # type: ignore[attr-defined]
    if settings is None:
        settings = Settings()
        app.state.settings = settings  # type: ignore[attr-defined]
    return settings


def get_crew_client(settings: Annotated[Settings, Depends(get_settings)]) -> CrewClient:
    client: CrewClient | None = getattr(app.state, "crew_client", None)  # type: ignore[attr-defined]
    if client is None:
        client = CrewClient(
            crew_url=settings.crew_url,
            cache_ttl=settings.crew_cache_ttl,
            timeout=settings.request_timeout,
        )
        app.state.crew_client = client  # type: ignore[attr-defined]
    return client


def get_track_client(settings: Annotated[Settings, Depends(get_settings)]) -> ISSTrackClient:
    client: ISSTrackClient | None = getattr(app.state, "track_client", None)  # type: ignore[attr-defined]
    if client is None:
        client = ISSTrackClient(
            tle_url=settings.tle_url,
            timeout=settings.request_timeout,
        )
        app.state.track_client = client  # type: ignore[attr-defined]
    return client


@app.on_event("startup")
async def startup_event() -> None:
    settings = Settings()
    app.state.settings = settings  # type: ignore[attr-defined]
    app.state.track_client = ISSTrackClient(  # type: ignore[attr-defined]
        tle_url=settings.tle_url,
        timeout=settings.request_timeout,
    )
    app.state.crew_client = CrewClient(  # type: ignore[attr-defined]
        crew_url=settings.crew_url,
        cache_ttl=settings.crew_cache_ttl,
        timeout=settings.request_timeout,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    crew_client: CrewClient | None = getattr(app.state, "crew_client", None)
    if crew_client:
        await crew_client.aclose()
    track_client: ISSTrackClient | None = getattr(app.state, "track_client", None)
    if track_client:
        await track_client.aclose()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True)


@app.get("/iss/now", response_model=ISSNowResponse)
async def iss_now(
    response: Response, track_client: Annotated[ISSTrackClient, Depends(get_track_client)]
) -> ISSNowResponse | JSONResponse:
    try:
        lat, lon, alt, velocity = await track_client.get_position_now()
    except TLEUnavailableError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc)},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    response.headers["Cache-Control"] = "max-age=5"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return ISSNowResponse(
        lat=lat,
        lon=lon,
        altitude_km=alt,
        velocity_kmh=velocity,
        timestamp=ts,
        source="tle/sgp4",
        stale=False,
    )


@app.get("/iss/history", response_model=ISSTrackResponse)
async def iss_history(
    response: Response,
    track_client: Annotated[ISSTrackClient, Depends(get_track_client)],
    hours: float = 1.0,
) -> ISSTrackResponse | JSONResponse:
    hours = max(0.25, min(24.0, hours))
    try:
        points = await track_client.get_track(hours)
    except TLEUnavailableError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc)},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    response.headers["Cache-Control"] = "max-age=60"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return ISSTrackResponse(hours=hours, points=points)


@app.get("/iss/crew", response_model=CrewResponse)
async def iss_crew(
    response: Response, crew_client: Annotated[CrewClient, Depends(get_crew_client)]
) -> CrewResponse | JSONResponse:
    try:
        payload = await crew_client.fetch()
    except CrewUnavailableError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc)},
            headers={
                "Cache-Control": f"max-age={crew_client.cache_ttl}",
                "Access-Control-Allow-Origin": "*",
            },
        )

    response.headers["Cache-Control"] = f"max-age={crew_client.cache_ttl}"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return payload
