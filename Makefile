.PHONY: up down logs test fmt backend-test frontend-test backend-fmt frontend-fmt

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test: backend-test frontend-test

backend-test:
	docker compose run --rm backend pytest -q

frontend-test:
	docker compose run --rm frontend npm run lint

fmt: backend-fmt frontend-fmt

backend-fmt:
	docker compose run --rm backend bash -lc "ruff check --fix app && black app"

frontend-fmt:
	docker compose run --rm frontend npm run format
