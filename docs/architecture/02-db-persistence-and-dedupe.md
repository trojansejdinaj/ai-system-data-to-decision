# DB persistence + idempotent ingestion (Week 04)

## Goal
Make ingestion durable and repeatable:
- data persists across app/DB restarts
- the same input can be ingested multiple times without creating duplicates

## Tables
### ingest_runs
Tracks each ingestion execution (provenance).

Key fields:
- `id` (UUID PK)
- `created_at`
- `source` (e.g., `samples`, `upload`)
- `status` (`started`, `success`, `failed`)
- `files` (newline-separated list)
- `error` (nullable)

### raw_records
Stores raw ingested rows (staging layer) and enforces dedupe.

Key fields:
- `id` (UUID PK)
- `run_id` (FK → ingest_runs.id)
- `payload` (JSONB original row)
- `source` (denormalized from ingest_runs)
- `source_id`, `event_time`, `category`, `value` (extracted required keys)
- `record_hash` (sha256 of normalized required keys)

Constraints + indexes:
- `UNIQUE (source, record_hash)` — prevents duplicates
- Indexes on: `record_hash`, `source`, `(source, event_time)`, `(source, source_id)`, `category`

## Dedupe strategy
- Compute a stable `record_hash` from the required schema keys.
- Insert with `ON CONFLICT DO NOTHING` using `(source, record_hash)`.

This makes ingestion **idempotent** without requiring a separate dedupe job.

## What this unlocks
- Safe replays of the same batch/file
- Reliable row counts for downstream transformation/model stages
- A clean baseline for later “silver/gold” tables (cleaned + feature-ready)
