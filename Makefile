.PHONY: sync fmt lint test run db-up db-down db-reset logs migrate revision

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

db-reset:
	docker compose down -v
	docker compose up -d
	$(MAKE) migrate

logs:
	docker compose logs -f

migrate: db-wait
	uv run alembic upgrade head

revision:
	uv run alembic revision -m "$(m)"

.PHONY: db-wait

db-wait:
	until docker compose exec -T db pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB >/dev/null 2>&1; do \
		echo "waiting for postgres..."; \
		sleep 1; \
	done
