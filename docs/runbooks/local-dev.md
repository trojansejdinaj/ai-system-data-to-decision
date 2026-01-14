# Local Development Runbook

This repo runs a **FastAPI** API server backed by a **Postgres** database (Docker Compose).  
Week 06 adds a **Dashboard v1** at `/dashboard` with DB-backed summary endpoints.

---

## Prerequisites

- Python **3.12+**
- **uv** installed
- Docker + Docker Compose
- (Optional) `psql` installed locally for DB access

---

## First-time setup

### 1) Install dependencies
```bash
make sync
```

### 2) Create `.env`
```bash
cp .env.example .env
```

Fill in the values (DB user/password/db name/ports). Never commit `.env`.

---

## One-command dev bring-up (recommended)

```bash
make dev-all
```

`dev-all` does:
- `docker compose up -d` (starts Postgres)
- waits for DB readiness
- `alembic upgrade head` (migrations)
- starts FastAPI via uvicorn with `--reload`

Open:
- Dashboard UI: `http://localhost:8000/dashboard`

---

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

---

## Dashboard v1 (Week 06)

### UI
- `GET /dashboard`  
  Browser: `http://localhost:8000/dashboard`

### API (JSON)
- `GET /dashboard/monthly`  
  Optional query params: `start` (inclusive), `end` (exclusive)

- `GET /dashboard/trend`  
  Required: `start`, `end`  
  Optional: `granularity=day|week|month`, `metric=total_records|distinct_records|distinct_source_ids|distinct_sources|distinct_categories`

Examples:
```bash
curl -s http://localhost:8000/dashboard/monthly

curl -s "http://localhost:8000/dashboard/trend?start=2025-12-15&end=2026-01-14&granularity=day&metric=total_records"
```

---

## Database access

### Option A: connect from host (recommended)
If Postgres is exposed on port **55432**:
```bash
psql -h localhost -p 55432 -U d2d_user -d d2d_db
```

### Option B: connect inside the container
```bash
docker compose exec -T db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Why `bash -lc`?
- it expands `$POSTGRES_USER` / `$POSTGRES_DB` **inside** the container where those env vars exist.

---

## Quick verification checklist

### 1) API is up
```bash
curl -i http://localhost:8000/health
```

### 2) Summary tables exist
Inside `psql`:
```sql
\dt summary.*
```

You should see:
- `summary.daily_metrics`
- `summary.monthly_metrics`

### 3) Dashboard endpoints return 200
```bash
curl -i http://localhost:8000/dashboard/monthly
curl -i "http://localhost:8000/dashboard/trend?start=2025-12-15&end=2026-01-14"
```

---

## Troubleshooting (fast)

### `ModuleNotFoundError: No module named 'app'`
This repo uses `src/` layout and imports like `from app...`.  
Run via Makefile (it sets `PYTHONPATH=src`) or run manually:

```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload --env-file .env
```

### `/dashboard/monthly` 500 with `AmbiguousParameter`
Cause: optional `start/end` passed as NULL without typed casting.  
Fix: cast params to `date` in SQL (e.g. `CAST(:start AS date)`).

---

## Command reference

| Command | What it does |
|---|---|
| `make dev-all` | Start DB, migrate, run API |
| `make run` | Run API with reload |
| `make db-up` | Start Postgres |
| `make db-down` | Stop containers |
| `make db-reset` | Destroy DB volume + recreate |
| `make migrate` | Apply migrations |
| `make revision m="..."` | Create migration |
| `make lint` | Ruff check/fix |
| `make test` | Pytest |
| `make logs` | Docker logs |
