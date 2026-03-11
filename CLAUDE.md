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
`GET /iss/now` → `ISSClient.fetch()` (in-process cache TTL=8s, rate limit=5s) → upstream `wheretheiss.at` API → normalized `ISSNowResponse`.

Key files:
- `backend/app/iss_client.py` — `ISSClient` with async lock, cache, and stale fallback logic
- `backend/app/models.py` — Pydantic `ISSNowResponse` (fields: `lat`, `lon`, `altitude_km`, `velocity_kmh`, `timestamp`, `source`, `stale`)
- `backend/app/serverless_handler.py` — Lambda entry point that reuses `ISSClient` directly (no FastAPI overhead)

Cache behavior: fresh cache returns immediately; if upstream fails, returns stale cache with `stale=True`; if no cache and upstream fails, raises `UpstreamUnavailableError` → 503.

### Frontend data flow
`App.tsx` polls `fetchIssNow()` (from `src/api.ts`) every 5 s → passes position + 15-min ground track breadcrumbs to `GlobeView` + telemetry to `Hud`.

Key files:
- `frontend/src/api.ts` — `fetchIssNow()` reads `VITE_API_URL` env var (default: `http://localhost:8000/iss/now`)
- `frontend/src/components/GlobeView.tsx` — Globe.gl instance managed via refs; separate `useEffect` hooks for init, position, and track updates
- `frontend/src/components/Hud.tsx` — displays telemetry + LIVE/STALE/ACQ pills

### Serverless path
CDK stack (`infra/lib/iss-live-stack.ts`) wires `backend/app/serverless_handler.py` as a `PythonFunction` behind API Gateway at `GET /iss/now`. The Lambda bundles the entire `backend/` directory.

## Environment Variables

Backend (`.env` / `backend/.env`): `UPSTREAM_URL`, `CACHE_TTL` (default 8s), `RATE_LIMIT_SECONDS` (default 5s), `REQUEST_TIMEOUT`.

Frontend (`frontend/.env`): `VITE_API_URL` — the backend URL polled by the browser.

Root `.env`: `BACKEND_PORT` / `FRONTEND_PORT` for Docker Compose port mapping.

## Code Style

- Backend: `black` (line length 100), `ruff` with `E,F,I,UP,B,ASYNC,S,RUF` rules, Python 3.12+
- Frontend: ESLint + Prettier, zero warnings policy (`--max-warnings=0`)
