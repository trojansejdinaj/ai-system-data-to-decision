# ai-system-data-to-decision

**Status:** ingestion + cleaning + idempotent DB persistence (Week 04).  
This repo is the flagship “data → decision” portfolio project: a production-style backbone for ingesting raw data, storing it, transforming it, training models, and serving decisions via APIs.

Right now it’s intentionally small and correct: FastAPI + Postgres + migrations + tests + a clean dev workflow —
plus ingestion v1, deterministic cleaning rules, and DB-enforced dedupe.

---

## What it can do today

- Run a FastAPI app with a health endpoint: `GET /health → {"status":"ok"}`
- Run Postgres 16 locally via Docker Compose (default host port **55432**)
- Manage dependencies with **uv** + `pyproject.toml` + `uv.lock`
- Run Alembic migrations via `make migrate` (with a DB readiness wait)
- Lint/format/test with one-liner Make targets

- Ingest CSV/XLSX:
  - `POST /ingest/samples` (loads `data/samples/`)
  - `POST /ingest/files` (multipart upload)
- Persist ingestion runs + raw records in Postgres
- Enforce idempotency (no duplicate raw rows) via DB unique constraint + upsert
- Cleaning + normalization module (`app.cleaning`) with unit tests

> Models/feature engineering/decision logic are not built yet — this is the foundation + ingestion + raw staging layer.

---

## Quickstart

### Prereqs
- Python **3.12+**
- `uv`
- Docker + Docker Compose

### 1) Install deps
```bash
make sync
```

### 2) Configure env
Create a real `.env` from the template and set your DB password:
```bash
cp .env.example .env
# edit .env and set POSTGRES_PASSWORD + DATABASE_URL
```

### 3) Start Postgres
```bash
make db-up
```

### 4) Run migrations
```bash
make migrate
```

### 5) Run the API
```bash
make run
```

Then verify:
```bash
curl http://localhost:8000/health
```

---

## Common commands

| Task | Command |
|------|---------|
| Install/sync deps | `make sync` |
| Format | `make fmt` |
| Lint (auto-fix) | `make lint` |
| Run tests | `make test` |
| Start API | `make run` |
| Start DB | `make db-up` |
| Stop DB | `make db-down` |
| Tail DB logs | `make logs` |
| Wait for DB | `make db-wait` |
| Apply migrations | `make migrate` |
| Create migration | `make revision m="your message"` |

---

## Configuration

### Environment variables
Local config is driven by `.env` (gitignored) and `.env.example` (committed).

Key vars:
- `POSTGRES_DB` (default: `d2d_db`)
- `POSTGRES_USER` (default: `d2d_user`)
- `POSTGRES_PASSWORD` (**required**)
- `POSTGRES_PORT` (default: **55432**)
- `DATABASE_URL` (used by app + Alembic)

Example (`.env.example`):
```env
POSTGRES_DB=d2d_db
POSTGRES_USER=d2d_user
POSTGRES_PASSWORD=__SET_IN_.ENV__
POSTGRES_PORT=55432

DATABASE_URL=postgresql+psycopg://d2d_user:__SET_IN_.ENV__@localhost:55432/d2d_db
```

---

## Database + migrations

- Postgres runs as a Docker service named `db`.
- Alembic is configured at `alembic.ini` and runs migrations from `src/app/db/migrations`.

Apply migrations:
```bash
make migrate
```

Create a migration:
```bash
make revision m="add_events_table"
```

### Note about autogenerate
`alembic/env.py` is wired to `Base.metadata`, so `alembic revision --autogenerate` can detect model changes.

### Note about dotenv
`alembic/env.py` uses `python-dotenv` (`from dotenv import load_dotenv`).
This repo includes it in `pyproject.toml` so migrations can load `.env` for local development.

---

## Project layout (current)

Typical structure:
```
.
├── src/
│   └── app/
│       ├── main.py
│       ├── api/
│       │   └── ingest.py
│       ├── ingestion/
│       │   └── service.py
│       ├── cleaning/
│       │   ├── pipeline.py
│       │   └── rules.py
│       ├── core/
│       │   └── config.py
│       └── db/
│           ├── models.py
│           ├── session.py
│           └── migrations/
├── tests/
│   ├── test_health.py
│   ├── test_ingest.py
│   └── test_cleaning_rules.py
├── data/
│   └── samples/
│       ├── sample.csv
│       └── sample.xlsx
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml
└── Makefile
```

---

## Docs

See `docs/` for:
- Runbooks (local dev, DB, migrations, troubleshooting)
- ADRs (architecture decisions)
- Changelog

Start at: `docs/00-index.md`

---

## Roadmap (next milestones)

1) **Persist cleaned rows (silver table)**
   - Run `app.cleaning` before persistence into a new `clean_records` table
   - Keep raw → clean lineage + replay

2) **Transform + feature layer (gold tables)**
   - Aggregations, time windows, and feature snapshots
   - Tests for deterministic transforms

3) **Decision API**
   - Start with rules/scoring
   - Add model serving once data volume + stability exist

---

## License
MIT (see `LICENSE`)
