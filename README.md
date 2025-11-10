# ISS Live

Local-first toolkit that fetches the International Space Station state locally, renders it on a Globe.gl-powered 3D globe, and keeps everything ready for an eventual serverless hand-off.

## Project Layout

```
iss-live/
  backend/        FastAPI app + shared ISS client logic
  frontend/       Vite + React globe dashboard
  infra/          AWS CDK (TypeScript) skeleton for API Gateway + Lambda
  docker-compose.yml
  Makefile
```

## Prerequisites

- Docker Desktop 4.0+
- Python 3.12 (if you want to run the backend outside Docker)
- Node.js 18+ and npm 9+ (if you want to run the frontend or infra tooling directly)

## Quick Start (Local, Docker)

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make up
# Frontend → http://localhost:5173
# Backend  → http://localhost:8000
```

The backend exposes:

- `GET /health` → `{ "ok": true }`
- `GET /iss/now` → normalized ISS telemetry with caching + graceful fallback. Response headers include `Cache-Control: max-age=8` and `Access-Control-Allow-Origin: *`.

## Make Targets

| Command | Description |
| --- | --- |
| `make up` | Build + start both services via Docker Compose (reload enabled). |
| `make down` | Stop and remove the stack. |
| `make logs` | Tail combined container logs. |
| `make test` | Run backend pytest suite + frontend ESLint checks inside containers. |
| `make fmt` | Run `ruff` + `black` for backend and `prettier` for frontend. |

## Backend Notes

- Stack: FastAPI + httpx with a tiny in-process cache (TTL 8s) and rate limit (≤1 upstream hit / 5s).
- Healthy path: warm-cache responses return within ~300 ms locally.
- Failure path: if `wheretheiss.at` is down, the API keeps returning the newest cached payload with `"stale": true`; only if there’s no cache do you see a `503 {"error": ...}`.
- Tooling: `pytest`, `ruff`, `black`. Run locally with `cd backend && .venv/bin/python -m pytest -q` once you create a virtualenv.

## Frontend Notes

- Stack: Vite + React + Globe.gl (Three.js).
- Poll cadence: every 5 s with camera easing + ground track (≈15 min of breadcrumbs).
- HUD shows lat/lon/altitude/velocity/source and LIVE/STALE pills; a toast appears if the local API becomes unreachable.
- Quality gates: `npm run lint`, `npm run format`, `npm run typecheck`, `npm run build`.

## Troubleshooting

- **CORS errors:** ensure you’re calling `http://localhost:8000/iss/now` (or the Compose hostname `http://backend:8000/iss/now`). The backend already emits permissive CORS headers.
- **Port collisions:** update `BACKEND_PORT` / `FRONTEND_PORT` inside `.env` before running `make up`.
- **Upstream ISS API down:** backend serves stale cache with `"stale": true`; frontend lights up the amber pill and keeps animating with last known coordinates.

## Tests & Linters

```bash
make test          # pytest + eslint
make fmt           # ruff/black + prettier
cd frontend && npm run typecheck
cd backend && .venv/bin/python -m pytest -q  # if you set up the venv locally
```

## Preparing for Serverless

A minimal AWS CDK skeleton lives in `infra/`:

- `GET /iss/now` REST API (API Gateway) backed by a Python 3.12 Lambda that reuses `backend/app/serverless_handler.py`.
- Env: `CACHE_TTL=8`, open CORS for `GET/OPTIONS`.
- Output: direct invoke URL (`IssApiUrl`).

When you’re ready to try it:

```bash
cd infra
npm install   # already done once to generate package-lock.json
npx cdk bootstrap
npx cdk synth
npx cdk deploy   # provisions API Gateway + Lambda (no secrets wired yet)
```

## Next Steps

- Capture a 10–20 s screen recording (GIF/MP4) of the globe view for sharing.
- Wire the CDK stack into your preferred CI/CD workflow once you’re comfortable with the local story.
