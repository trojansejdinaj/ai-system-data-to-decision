.PHONY: sync fmt lint test run db-up db-down logs migrate revision

sync:
	uv sync

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

test:
	uv run pytest -q

run:
	uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

db-up:
	docker compose up -d

db-down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision -m "$(m)"
