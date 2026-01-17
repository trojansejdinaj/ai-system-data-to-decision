.PHONY: \
	sync fmt lint test run dev-all \
	db-up db-down db-reset db-wait \
	logs migrate revision metrics \
	test-integration

sync:
	uv sync

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

test:
	uv run pytest -q -m "not integration"

test-integration:
	uv run pytest -q -m integration

# Keep "from app..." imports working with src-layout:
# - PYTHONPATH=src makes src/app importable as "app"
run:
	PYTHONPATH=src uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env

# Full local dev bring-up: start db, migrate, run api
dev-all: db-up migrate run

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

db-wait:
	until docker compose exec -T db pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB >/dev/null 2>&1; do \
		echo "waiting for postgres..."; \
		sleep 1; \
	done

migrate: db-wait
	uv run alembic upgrade head

revision:
	uv run alembic revision -m "$(m)"

metrics:
	@docker compose exec -T db bash -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" < src/app/transform/monthly_metrics.sql'
	@docker compose exec -T db bash -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c "SELECT * FROM summary.monthly_metrics ORDER BY month_start;"'
