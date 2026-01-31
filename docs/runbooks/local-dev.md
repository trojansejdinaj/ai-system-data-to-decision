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

**Option: Use direnv instead (or alongside)**

Create `.envrc` to auto-load .env:
```bash
echo 'dotenv' > .envrc
direnv allow
```

✅ **Note:** `.env` stays gitignored; `.envrc` is safe to commit.

### 3) One-command dev bring-up (recommended)
```bash
make dev-all
```

**What dev-all does:**

- docker compose up -d (start Postgres)
- waits for DB readiness
- uv run python -m alembic upgrade head (apply migrations)
- starts FastAPI via uvicorn with --reload

**Open:**

- Dashboard UI: http://localhost:8000/dashboard

## Portfolio demo flow

**The golden path (T1 DoD):**
```bash
make demo
```

**What demo does (in order):**

1. `make db-up` — start Postgres container
2. `make migrate` — apply latest migrations
3. `make ingest-samples` — run CLI ingestion (no API needed)
4. `make flags` — run exceptions/flags engine
5. Print latest pipeline_runs (5 rows)
6. Print record counts (raw_records, ingest_runs)
7. Exit with success banner

**Prove idempotency: run it twice**
```bash
make demo
make demo  # run again immediately
```

**Expected on run #2:**
- `inserted_records: 0` (samples already in DB)
- `deduped_records: 20` (recognizes duplicates)
- `raw_records` stays at 10 rows (deduplication working)
- Both pipeline_runs appear in the output

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

**CLI (used by `make demo`):**
```bash
make ingest-samples
```
✅ Does **not** require FastAPI running. Used in the golden path.

**Tables:**
- public.ingest_runs
- public.raw_records

**Alternative: API endpoint (requires `make run` in another terminal)**
```bash
curl -s -X POST http://localhost:8000/ingest/samples | python -m json.tool
```
Or via the dashboard UI.

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

**Fix (preferred): direnv**

```bash
echo 'dotenv' > .envrc
direnv allow
```

Then re-run in the same shell:

```bash
make flags
make clean
make metrics
```

**Fix (fallback): manual env load**

```bash
set -a
source .env
set +a
make flags
make clean
make metrics
```