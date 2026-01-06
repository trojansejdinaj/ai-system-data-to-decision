# Week 02 — Ingestion v1 (CSV / XLSX)

## Summary
Implemented the first production-grade ingestion layer for the system.

The focus of this week was to prove that the system can reliably ingest
structured files, validate schema contracts, persist raw data, and track
ingestion runs end-to-end.

No ML or normalization was introduced in this phase.

---

## Features added

### Ingestion endpoints
- `POST /ingest/samples`
  - Loads local sample files from `data/samples/`
- `POST /ingest/files`
  - Accepts uploaded CSV and XLSX files via multipart form data

Both endpoints execute the same ingestion pipeline.

---

### Supported file types
- CSV (`.csv`)
- Excel (`.xlsx`)

---

### Schema validation
All ingested files must contain the following columns:
- `source_id`
- `event_time`
- `value`
- `category`

If validation fails:
- ingestion is aborted
- no partial writes occur
- API returns `400 Bad Request`

---

### Database tables introduced

#### `ingest_runs`
Tracks ingestion executions.
- UUID primary key
- UTC, timezone-aware timestamps
- Source, status, filenames, error tracking

#### `raw_records`
Stores raw ingested rows.
- One row per ingested record
- Linked to `ingest_runs` via `run_id`
- Payload stored as JSONB

---

### Tests
Integration tests added to validate:
- Successful ingestion via `/ingest/samples`
- CSV and XLSX parsing
- Schema validation failures

All tests passing.

---

## Status
- Ingestion v1 complete
- Test suite green
- Ready for normalization phase
