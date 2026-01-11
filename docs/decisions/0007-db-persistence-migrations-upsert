# ADR 0007 — DB persistence, migrations, and idempotent upserts

## Status
Accepted — 2026-01-26

## Context
Week 02 introduced ingestion into Postgres (`ingest_runs`, `raw_records`).
However, repeated ingestions of the same files created duplicate `raw_records` rows.

For a data→decision system, ingestion must be **idempotent**:
- the same input can be re-run safely
- data persists across restarts
- re-processing does not inflate downstream metrics

We also want correctness enforced by the database, not only by application code.

## Decision
1. Keep Postgres as the durable store and Alembic as the schema change mechanism.
2. Add deterministic dedupe keys to `raw_records`:
   - `source`, `source_id`, `event_time`, `category`, `value`
   - `record_hash` computed from the required keys
3. Enforce dedupe at the DB layer with a unique constraint:
   - `UNIQUE (source, record_hash)`
4. Implement ingestion writes using Postgres upsert semantics:
   - `INSERT ... ON CONFLICT DO NOTHING`
   - conflict target matches the unique constraint
5. Add supporting indexes for common access patterns.

## Consequences
### Positive
- Ingestion becomes repeatable and safe (no duplicate raw rows).
- Database enforces correctness even if app logic changes.
- Better query performance via indexes.
- Schema changes are reviewable and reproducible via migrations.

### Tradeoffs
- We store denormalized key columns in `raw_records` (slightly more storage).
- Duplicate rows are dropped, which means later ingestion runs won't “own” the duplicated records (the record remains linked to the first run that inserted it).
- Hashing logic must remain stable (changing normalization rules changes `record_hash`).

## Implementation notes
- Migration adds columns, backfills existing rows, then enforces NOT NULL + constraints.
- The hash is computed from required keys only (stable across files/runs).
- Validation is done via integration test: ingest the same dataset twice and ensure row counts do not grow.

## Follow-ups
- Consider a separate association table if we later want to track “record seen in run” without duplicating raw records.
- Promote selected raw keys into a cleaned/staged table once normalization is wired into persistence.
