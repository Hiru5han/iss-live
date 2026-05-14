# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local Development (Docker)
```bash
make up        # Build + start both services with hot reload
make down      # Stop and remove the stack
make logs      # Tail combined container logs
make test      # Run backend pytest + frontend ESLint
make fmt       # Run ruff/black (backend) + prettier (frontend)
```

### Backend (direct, requires virtualenv at backend/.venv)
```bash
cd backend && .venv/bin/python -m pytest -q          # Run all tests
cd backend && .venv/bin/python -m pytest app/tests/test_iss_now.py -q  # Single test file
cd backend && .venv/bin/ruff check app && black app  # Lint + format
```

### Frontend (direct)
```bash
cd frontend && npm run dev        # Dev server
cd frontend && npm run lint       # ESLint (zero warnings allowed)
cd frontend && npm run typecheck  # tsc --noEmit
cd frontend && npm run format     # Prettier
cd frontend && npm run build      # Type-check + Vite build
```

### Infrastructure (CDK)
```bash
cd infra && npx cdk synth   # Synthesize CloudFormation
cd infra && npx cdk deploy  # Deploy to AWS
```

## Architecture

Three independent packages sharing no build system:

```
backend/   FastAPI (Python 3.12) — app/main.py is the ASGI entrypoint
frontend/  Vite + React + Globe.gl (TypeScript)
infra/     AWS CDK (TypeScript) — deploys API Gateway + Lambda
```

### Backend data flow
`GET /iss/now` → `ISSTrackClient.get_position_now()` → SGP4 propagation from cached TLE data → `ISSNowResponse` (source: `"tle/sgp4"`).

`GET /iss/history?hours=N` → `ISSTrackClient.get_track(hours)` → SGP4 positions sampled every minute → `ISSTrackResponse`.

`GET /iss/crew` → `CrewClient.fetch()` → `open-notify.org` API → `CrewResponse`.

Key files:
- `backend/app/iss_track_client.py` — `ISSTrackClient`: fetches TLE from Celestrak (cached 1 h), exposes `get_position_now()` for live position and `get_track(hours)` for history; uses SGP4 + WGS-84 geodetic conversion
- `backend/app/crew_client.py` — `CrewClient` with TTL cache and stale fallback
- `backend/app/models.py` — Pydantic models: `ISSNowResponse` (fields: `lat`, `lon`, `altitude_km`, `velocity_kmh`, `timestamp`, `source`, `stale`), `ISSTrackResponse`, `CrewResponse`
- `backend/app/serverless_handler.py` — Lambda entry point; shares the same `ISSTrackClient` singleton for both `/iss/now` and `/iss/history`

### Frontend data flow
`App.tsx` polls `fetchIssNow()` every 5 s and `fetchIssHistory(hours)` every 60 s → passes position to `GlobeView` + telemetry to `Hud`; crew is polled every 5 min.

Key files:
- `frontend/src/api.ts` — `fetchIssNow()`, `fetchIssHistory()`, `fetchCrew()`; base URL from `VITE_API_BASE` or stripped `VITE_API_URL` (default: `http://localhost:8000`)
- `frontend/src/components/GlobeView.tsx` — Globe.gl instance managed via refs; separate `useEffect` hooks for init, position, and trail updates
- `frontend/src/components/Hud.tsx` — displays telemetry + LIVE/STALE/ACQ pills
- `frontend/src/components/TrailSelector.tsx` — selects history window (15 min → 24 h)

### Serverless path
CDK stack (`infra/lib/iss-live-stack.ts`) wires `backend/app/serverless_handler.py` as a `PythonFunction` behind API Gateway at `GET /iss/now`, `GET /iss/history`, and `GET /iss/crew`. CloudFront proxies `/iss/*` to API Gateway so the frontend can call relative URLs.

## Environment Variables

Backend (`.env` / `backend/.env`): `TLE_URL` (default: Celestrak CATNR=25544), `REQUEST_TIMEOUT`, `CREW_URL`, `CREW_CACHE_TTL`.

Frontend (`frontend/.env`): `VITE_API_URL` — used to derive the API base URL (strip `/iss/now` suffix). In production the deploy workflow sets this to `/iss/now` so calls are relative to the CloudFront domain.

Root `.env`: `BACKEND_PORT` / `FRONTEND_PORT` for Docker Compose port mapping.

## Code Style

- Backend: `black` (line length 100), `ruff` with `E,F,I,UP,B,ASYNC,S,RUF` rules, Python 3.12+
- Frontend: ESLint + Prettier, zero warnings policy (`--max-warnings=0`)
