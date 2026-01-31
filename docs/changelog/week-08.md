# Week 08 — Reliability: structured logs + run tracking

## Goal
Failures yield clear, actionable logs and each pipeline run is traceable end-to-end:
- `run_id` added everywhere
- step timing captured
- run status stored in DB (`running/succeeded/failed`)
- proof screenshots for logs + runs table

## What shipped
### Structured logs (JSON)
- Logs are emitted as JSON with consistent fields.
- Every event includes `run_id` + `pipeline`.
- Failures include `error_type` + `error_message` and the step that failed.

### Run tracking (DB)
- New `pipeline_runs` table captures:
  - `pipeline`, `status`
  - `started_at`, `finished_at`, `duration_ms`
  - `records_in` (Integer, nullable), `records_out` (Integer, nullable)
  - `error_summary` (Text, nullable)
  - `steps` (JSON array of step results)
  - `error_type`, `error_message` (on failures)
- Implemented `RunTracker` + `StepTimer` pattern used by pipelines.

## Output artifacts
- Screenshot proof: structured logs (showing `run_id`, step timing, `run_succeeded`):
  - `docs/assets/week-08/01-structured-logs.png`
- Screenshot proof: DB `pipeline_runs` row(s):
  - `docs/assets/week-08/02-pipeline-runs-table.png`

## How to run
### Unit tests (fast)
- `uv run pytest -q`

### Integration test (DB-backed)
- Load env:
  - `export $(grep -v '^#' .env | xargs)`
- Run:
  - `uv run pytest -q -m integration`

### Proof run (flags pipeline)
- `uv run python -m app.flags`

### DB evidence query
- `docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pipeline,status,duration_ms,started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 10;"`

## Evidence
Store two screenshots:
1) Terminal output showing JSON logs with:
   - `run_id`
   - `step_*` events with `duration_ms`
   - `run_succeeded` (or `run_failed`)
2) DB query output showing a new row in `pipeline_runs` for the pipeline you ran.
