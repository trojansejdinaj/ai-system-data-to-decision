# Local Development Runbook

This repo runs a **FastAPI** API server backed by a **Postgres** database (Docker Compose).
It also includes a small pipeline stack:

- **Bronze:** `public.raw_records` (ingestion)
- **Silver:** `clean.clean_records` (cleaning)
- **Gold:** `summary.monthly_metrics` (transform view)
- **Reliability:** `pipeline_runs` run tracking + structured logs

---

## Prerequisites
- Python **3.12+**
- **uv**
- Docker + Docker Compose
- (Optional) `psql` locally

---

## First-time setup

### 1) Install dependencies
```bash
make sync
```

### 2) Create .env
```bash
cp .env.example .env
```

Fill in DB creds (at minimum POSTGRES_PASSWORD) and set DATABASE_URL.

### 3) One-command dev bring-up (recommended)
```bash
make dev-all
```

**What dev-all does:**

- docker compose up -d (start Postgres)
- waits for DB readiness
- alembic upgrade head (apply migrations)
- starts FastAPI via uvicorn with --reload

**Open:**

- Dashboard UI: http://localhost:8000/dashboard

## Portfolio demo flow

**Option A: one-liner demo**
```bash
make demo
```

**What demo does (conceptually):**

- Ingest sample CSV/XLSX into raw_records
- Run flags report (writes CSV)
- Print latest pipeline runs

**Option B: step-by-step**
```bash
make demo-ingest
make flags
make clean
make metrics
make runs
```

**Expected outputs:**

- Flags CSV: docs/assets/week-07/flags_report.csv
- Monthly metrics: queryable via summary.monthly_metrics
- Run tracking: make runs

## Common commands

### Start/stop DB
```bash
make db-up
make db-down
```

### Reset DB (destructive: deletes volume)
```bash
make db-reset
```

### Run migrations
```bash
make migrate
```

### Create a new migration
```bash
make revision m="your message"
```

### Run API only (hot reload)
```bash
make run
```

### Lint and tests
```bash
make lint
make test
```

### Tail docker logs
```bash
make logs
```

## Pipelines

### Ingestion (Bronze)

**Endpoint:** `POST /ingest/samples`

**Tables:**

- public.ingest_runs
- public.raw_records

**Example:**
```bash
curl -s -X POST http://localhost:8000/ingest/samples | python -m json.tool
```

### Flags (Exceptions)
```bash
make flags
```

**Produces:**

- docs/assets/week-07/flags_report.csv
- a pipeline_runs row with step-level metadata

### Cleaning (Silver)
```bash
make clean
```

**Upserts into:**

- clean.clean_records

### Metrics refresh (Gold view)
```bash
make metrics
```

**Creates/refreshes:**

- summary.monthly_metrics (VIEW)
- summary.data_quality_checks (TABLE)

## Database access

**Option A: connect from host**
```bash
psql -h localhost -p 55432 -U d2d_user -d d2d_db
```

**Option B: connect inside the container**
```bash
docker compose exec -T db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Troubleshooting

### Port already in use (Address already in use)

If you ran `make dev-all` and then also ran `make run` in another terminal, you'll collide on port 8000.

**Fix options:**

- stop the old uvicorn (CTRL+C in the terminal that started it), OR
- run only one server process, OR
- change the port in the `make run` command if you really need two

### DATABASE_URL is required when running flags/clean/metrics

Your pipeline CLIs need DB access.

**Fix (quick):**

```bash
set -a
source .env
set +a
```

Then re-run:

```bash
make flags
make clean
make metrics
```