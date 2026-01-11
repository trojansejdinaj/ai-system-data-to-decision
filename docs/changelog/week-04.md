# Week 04 — DB persistence + migrations (2026-01-26)

## Goal
Ensure data persists across runs **with no duplicates**, backed by a real schema (constraints + indexes) and reproducible **Alembic migrations**.

## What shipped
- **Idempotent ingestion writes** via Postgres `ON CONFLICT DO NOTHING`.
- **Raw record dedupe keys** added to `raw_records`:
  - `source`, `source_id`, `event_time`, `category`, `value`, `record_hash`
- **Unique constraint** on `(source, record_hash)` to enforce dedupe in the database.
- **Indexes** added for the main access patterns:
  - `record_hash`, `source`, `(source, event_time)`, `(source, source_id)`, `category`
- **Migration** to backfill keys for existing rows and then enforce `NOT NULL` + constraints.
- **Integration test** proving raw records do not grow when ingesting the same data twice.

## Key behavior (why this matters)
- Re-running `/ingest/samples` (or uploading the same file again) no longer balloons `raw_records`.
- The database becomes the source of truth for dedupe (app logic helps, but DB enforces).

## Migration added
- `src/app/db/migrations/versions/c7b2d771f7a0_raw_record_dedupe_keys.py`

## Validation
1) Apply migrations:
```bash
make db-up
make migrate
```

2) Ingest the samples twice:
```bash
curl -X POST http://localhost:8000/ingest/samples
curl -X POST http://localhost:8000/ingest/samples
```

3) Confirm row counts are stable:
```bash
docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT COUNT(*) AS raw_records FROM raw_records;"
```
The second ingest should not increase `raw_records`.

## Proof artifacts
- Migration file committed (see above).
- Screenshot required for portfolio proof:
  - DB tool showing `ingest_runs` + `raw_records` tables, and that `raw_records` has:
    - unique constraint `uq_raw_records_source_record_hash`
    - key indexes

Suggested path for the screenshot:
- `docs/assets/week04/db-tables.png`
