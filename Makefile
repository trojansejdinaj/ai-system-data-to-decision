# Makefile — AI System: Data-to-Decision
# Local dev shortcuts (db + migrations + API) and portfolio demo commands.

SHELL := /bin/bash

PYTHONPATH := src
API_HOST ?= 0.0.0.0
API_PORT ?= 8000
ENV_EXPORT := set -a; source .env; set +a;

.PHONY: \
	sync fmt lint test test-integration \
	run dev-all \
	db-up db-down db-reset db-wait logs \
	migrate revision metrics \
	ingest-samples flags runs demo clean refresh

# --- Python env --------------------------------------------------------------

sync:
	uv sync

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

test:
	uv run python -m pytest -q -m "not integration"

test-integration:
	uv run python -m pytest -q -m integration

# --- App ---------------------------------------------------------------------

# Keep "from app..." imports working with src-layout:
# - PYTHONPATH=src makes src/app importable as "app"
run:
	PYTHONPATH=$(PYTHONPATH) uv run uvicorn app.main:app --reload --host $(API_HOST) --port $(API_PORT) --env-file .env

# Full local dev bring-up: start db, migrate, run api
dev-all: db-up migrate run

# --- Database (docker compose) -----------------------------------------------

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
	@$(ENV_EXPORT) \
	until docker compose exec -T db pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" >/dev/null 2>&1; do \
		echo "waiting for postgres..."; \
		sleep 1; \
	done

# --- Migrations / transforms --------------------------------------------------

migrate: db-wait
	@$(ENV_EXPORT) \
	uv run python -m alembic upgrade head

# usage: make revision m="add pipeline_runs table"
revision:
	uv run python -m alembic revision -m "$(m)"

metrics:
	@$(ENV_EXPORT) \
	PYTHONPATH=$(PYTHONPATH) uv run python -m app.transform
	@$(ENV_EXPORT) \
	docker compose exec -T db psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c \
	"SELECT * FROM summary.monthly_metrics ORDER BY month_start;"

# --- Portfolio demo helpers ---------------------------------------------------

ingest-samples:
	@$(ENV_EXPORT) \
	PYTHONPATH=$(PYTHONPATH) uv run python -m app.ingestion --samples

# Keep the old API curl behaviour as an opt-in target
ingest-samples-api:
	curl -s -X POST http://localhost:$(API_PORT)/ingest/samples | python -m json.tool

clean:
	@$(ENV_EXPORT) \
	PYTHONPATH=$(PYTHONPATH) uv run python -m app.cleaning

flags:
	@set -a; source .env; set +a; \
	PYTHONPATH=$(PYTHONPATH) uv run python -m app.flags

runs:
	@$(ENV_EXPORT) \
	docker compose exec -T db psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c \
	"SELECT pipeline, id AS run_id, status, duration_ms, started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 10;"

refresh: clean metrics

demo:
	@set -euo pipefail; \
	echo "============================================================"; \
	echo "D2D DEMO — golden path"; \
	echo "Steps: services up → migrate → ingest(samples) → flags → summary"; \
	echo "============================================================"; \
	$(MAKE) db-up >/dev/null; \
	$(MAKE) migrate >/dev/null; \
	echo ""; \
	echo "--- ingest (samples) ---"; \
	$(ENV_EXPORT) PYTHONPATH=$(PYTHONPATH) uv run python -m app.ingestion --samples; \
	echo ""; \
	echo "--- flags ---"; \
	$(ENV_EXPORT) PYTHONPATH=$(PYTHONPATH) uv run python -m app.flags; \
	echo ""; \
	echo "--- recent pipeline_runs ---"; \
	$(ENV_EXPORT) docker compose exec -T db psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c \
	"SELECT pipeline, id AS run_id, status, duration_ms, started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;"; \
	echo ""; \
	echo "--- record counts ---"; \
	$(ENV_EXPORT) docker compose exec -T db psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c \
	"SELECT 'raw_records' AS table, COUNT(*) AS rows FROM raw_records UNION ALL SELECT 'ingest_runs', COUNT(*) FROM ingest_runs;"; \
	echo ""; \
	echo "✅ END BANNER: make demo succeeded"; \
	echo "============================================================"
