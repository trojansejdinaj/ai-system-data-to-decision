# Reliability: run tracking + structured logs

## Objective

Make every pipeline run observable and diagnosable:

- correlate all log lines using `run_id`
- measure per-step timing
- persist run status in DB
- keep a consistent "pipeline story" across CLI + API triggered flows

**Pipelines covered:**

- `ingest` (API: `/ingest/samples`)
- `flags` (CLI: `make flags`)
- `clean` (CLI: `make clean`)  ✅ Silver layer
- `metrics` (CLI: `make metrics`) ✅ Gold refresh runner

---

## Core design

### Run lifecycle

1) Generate `run_id` at pipeline start.
2) Insert a `pipeline_runs` row with status `running`.
3) For each step:
   - log `step_started`
   - measure duration
   - log `step_succeeded` or `step_failed`
   - append step result into `steps[]`
4) On success:
   - update row to `succeeded` + timing + steps
5) On failure:
   - update row to `failed` + timing + error fields + steps

### Structured logs

Events are JSON objects with consistent fields:

- `run_id` (UUID string)
- `pipeline` (e.g. `ingest`, `flags`, `clean`, `metrics`)
- `message` (event type, e.g. `run_started`, `step_started`)
- `step` (for step events)
- `duration_ms` (for completed steps/run)
- `meta` (optional JSON payload for step/run context)
- `error_type`, `error_message` (on failures)

### Step naming conventions

Keep step names stable over time so dashboards/alerts can rely on them.

**Examples:**

- `ingest`: `parse`, `upsert`
- `flags`: `fetch_raw_records`, `flag_records`, `write_flag_report_csv`
- `clean`: `fetch_raw_records`, `upsert_clean_records`
- `metrics`: `apply_sql`

---

## Database schema (v1)

**Table:** `pipeline_runs`

- `id` (UUID, PK)  -> `run_id`
- `pipeline` (text)
- `status` (running/succeeded/failed)
- `started_at`, `finished_at`
- `duration_ms`
- `records_in` (Integer, nullable) — optional processed input count
- `records_out` (Integer, nullable) — optional produced output count
- `error_summary` (Text, nullable) — short human-friendly error summary
- `input_ref` (optional string identifier, e.g. filename or sql path)
- `meta` (JSON)
- `steps` (JSON array of `{step,status,duration_ms,...}`)
- `error_type`, `error_message` (optional)

---

## Implementation touchpoints

### Logging

[app/observability/logging.py](app/observability/logging.py) provides JSON log formatting.

Log lines include `run_id`, `pipeline`, `step`, and optional `meta`.

### Run tracking

[app/observability/run_tracking.py](app/observability/run_tracking.py) provides:

- `RunTracker` for run lifecycle persistence
- `StepTimer` (or equivalent) for timing steps and emitting consistent events

### Pipeline entrypoints (where tracking happens)

**Ingest:**

- triggered from API route `/ingest/samples`
- wraps work using a `RunTracker(pipeline="ingest")`

**Flags:**

- CLI: `python -m app.flags` (via `make flags`)
- writes report CSV and persists run steps

**Clean (Silver):**

- CLI: `python -m app.cleaning` (via `make clean`)
- reads from `public.raw_records` and upserts into `clean.clean_records`

**Metrics (Gold refresh runner):**

- CLI: `python -m app.transform` (via `make metrics`)
- reads [src/app/transform/monthly_metrics.sql](src/app/transform/monthly_metrics.sql)
- executes SQL statements and persists the run

> **Note:** metrics are run via a Python runner (not container file redirection) so the refresh is both reproducible and tracked in `pipeline_runs`.

---

## Operational usage

### Inspect recent runs

```bash
make runs
```

**Expected:** you should see recent rows like:

- `ingest | succeeded`
- `flags | succeeded`
- `clean | succeeded`
- `metrics | succeeded`

### Debug a failure

Find the latest failed run in `pipeline_runs`.

Inspect `error_type`, `error_message`.

Check `steps[]` to identify which step failed and its duration.

Correlate with structured logs using the same `run_id`.

### Verification

**Happy path (portfolio proof)**

```bash
make demo
make clean
make metrics
make runs
```

**Expected:**

- `demo` ingests samples + writes flags CSV
- `clean` upserts into `clean.clean_records`
- `metrics` refreshes `summary.monthly_metrics`
- `pipeline_runs` contains `succeeded` entries for each pipeline

### Tests

Unit tests validate `RunTracker` behavior without a real DB.

Integration tests run pipelines and assert:

- a new `pipeline_runs` row exists
- `status` is `succeeded`
- `duration_ms` and `steps` are populated