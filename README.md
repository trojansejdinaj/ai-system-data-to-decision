````md
# AI System: Data-to-Decision (Portfolio)

A minimal, end-to-end data pipeline that turns messy source files into decision-ready metrics — with **ingestion**, **cleaning/normalization**, **transform layer**, a **dashboard**, **flags (exceptions)**, and **reliability run tracking** (structured logs + persisted pipeline run records).

**Status:** ✅ Weeks 01–08 complete (scaffold → ingest → clean → DB → transforms → dashboard → flags → run tracking)

---

## What it can do today (end-to-end)

### Ingest (Bronze)
- Load sample **CSV/Excel** sources into a raw schema/table (idempotent-ish for local dev)
- Validate environment + DB readiness before running

### Clean + Normalize
- Normalize key fields (dates, amounts, category mapping, source fields)
- Enforce consistent record shape so downstream transforms are stable
- Unit-tested cleaning rules

### Transform (Gold / Summary)
- Build monthly rollups/metrics (e.g., totals, distinct counts) in a summary schema/table/view
- Queryable from API endpoints used by the dashboard

### Dashboard (FastAPI)
- Serve a simple dashboard UI + JSON endpoints for charts/metrics
- Shows monthly metrics and trends computed from the transform layer

### Flags (Exceptions / Needs-attention)
- Run a “flags” pass to detect suspicious or invalid records
- Writes a CSV report under `docs/assets/week-07/` (portfolio proof artifact)

### Reliability: structured logs + run tracking
- Emits structured logs (JSON-like) with trace IDs
- Persists each pipeline execution into a `pipeline_runs` table (status, timestamps, duration, counts)

---

## 2-minute demo (portfolio proof)

### 1) Bring up DB + migrate + run API
```bash
make dev-all
```

### 2) Ingest sample files (CSV + XLSX)

```bash
curl -X POST http://localhost:8000/ingest/samples
```

### 3) Open the dashboard

* [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

### 4) Generate the flags report (writes CSV + tracks the run)

```bash
# In a second terminal:
PYTHONPATH=src uv run python -m app.flags
# (If your repo provides a CLI entrypoint, use that instead.)
```

### 5) Proof query: check persisted run tracking

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
"SELECT pipeline, status, duration_ms, started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 10;"
```

---

## Why this exists (portfolio intent)

This repo is a clean “systems” demonstration:

* You can ingest imperfect real-world files
* Normalize them into a consistent model
* Produce decision-ready rollups (monthly metrics)
* Expose them through an API/dashboard
* Detect exceptions (flags) and produce an artifact report
* Track and audit pipeline executions (run tracking)

If you want to hire someone to build practical pipelines and dashboards with reliability baked in, this is the type of work.

---

## Tech stack

* Python + FastAPI
* Postgres (Docker Compose)
* Alembic migrations
* Pytest
* `uv` for env + dependency management
* Makefile for repeatable local workflows

---

## Project structure

```text
src/
  app/
    api/                # FastAPI routes (dashboard, ingest, etc.)
    db/                 # DB session, models, migrations integration
    flags/              # Flags pipeline (exceptions report)
    ingest/             # Ingestion pipeline (CSV/XLSX)
    transform/          # Monthly metrics / summary transforms
    observability/      # structured logs + run tracking helpers (if present)
docs/
  00-index.md           # docs entry point
  architecture/         # architecture notes per week/module
  decisions/            # ADRs
  changelog/            # weekly changelogs
  assets/
    week-07/            # flags report CSV proof artifacts
    week-08/            # screenshots for logs/run tracking/dashboard
tests/                  # unit/integration tests
docker-compose.yml      # Postgres for local dev
Makefile                # one-command workflows
```

---

## Setup

### Requirements

* Docker + Docker Compose
* Python (managed via `uv`)
* Optional: `psql` client (or use `docker compose exec`)

### Environment variables

Copy the example env file and adjust if needed:

```bash
cp .env.example .env
```

Common variables:

* `DATABASE_URL` (or individual `POSTGRES_*` variables used by compose)
* `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

---

## Local development

### Bring everything up

```bash
make dev-all
```

### Run migrations

```bash
make migrate
```

### Run tests

```bash
make test
```

### Run lint/format (if configured)

```bash
make lint
```

---

## Key API endpoints

> Exact routes may vary slightly depending on the final implementation; check `src/app/api/` if needed.

* `POST /ingest` — ingest default/sample inputs
* `POST /ingest/samples` — ingest bundled samples (recommended for demo)
* `GET /dashboard` — dashboard UI
* `GET /dashboard/monthly` — monthly metrics (JSON)
* `GET /dashboard/trend` — trend view (JSON)

---

## Outputs / proof artifacts

* Flags report CSV:

  * `docs/assets/week-07/flags_report.csv` (or similarly named)
* Week 08 screenshots:

  * `docs/assets/week-08/01-structured-logs.png`
  * `docs/assets/week-08/02-pipeline-runs-table.png`

---

## Reliability: run tracking

Each pipeline execution writes a row to `pipeline_runs`, capturing:

* pipeline name (e.g., ingest / transform / flags)
* status (success/failure)
* timestamps + duration
* record counts (if captured)
* trace ID (if wired through)

This gives you auditability and makes it obvious when something breaks.

---

## Docs map

Start here:

* `docs/00-index.md`

Architecture and decisions:

* `docs/architecture/`
* `docs/decisions/`

Weekly timeline:

* `docs/changelog/`

---

## Roadmap (next steps to make it “production-ish”)

If you want to push this from “portfolio pipeline” to “mini production system”:

1. **Silver layer table**

   * Persist cleaned/normalized records in a `clean.*` schema/table
   * Keep raw (bronze) immutable; rebuild clean deterministically

2. **Deterministic refresh job**

   * Add a single command to rebuild transforms end-to-end
   * Example: `uv run python -m app.refresh` (and track the run)

3. **Request-level tracing**

   * Middleware that attaches request IDs and propagates them into pipeline runs/logs

4. **CI**

   * GitHub Actions: lint + unit tests + integration tests using a Postgres service

---

## License

See `LICENSE`.
