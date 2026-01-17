# Reliability: run tracking + structured logs

## Objective
Make every pipeline run observable and diagnosable:
- correlate all log lines using `run_id`
- measure per-step timing
- persist run status in DB

## Core design

### Run lifecycle
1) Generate `run_id` at pipeline start.
2) Insert `pipeline_runs` row with status `running`.
3) For each step:
   - log `step_started`
   - measure duration
   - log `step_succeeded` or `step_failed`
4) On success:
   - update row to `succeeded` + timing + steps
5) On failure:
   - update row to `failed` + timing + error fields + steps

### Structured logs
Events are JSON objects with consistent fields:
- `run_id` (UUID string)
- `pipeline` (e.g. `ingest`, `flags`)
- `message` (event type, e.g. `step_started`)
- `step` (for step events)
- `duration_ms` (for completed steps/run)
- `error_type`, `error_message` (on failures)

## Database schema (v1)
Table: `pipeline_runs`
- `id` (UUID, PK)  -> `run_id`
- `pipeline` (text)
- `status` (running/succeeded/failed)
- `started_at`, `ended_at`
- `duration_ms`
- `input_ref` (optional)
- `meta` (JSON)
- `steps` (JSON array of `{step,status,duration_ms,...}`)
- `error_type`, `error_message` (optional)

## Implementation touchpoints
- `app/observability/logging.py` provides JSON log formatting.
- `app/observability/run_tracking.py` provides `RunTracker` + `StepTimer`.
- Pipeline entrypoints wrap work in timed steps.

## Verification
- Unit tests validate run tracker behavior without a real DB.
- Integration test runs a pipeline and asserts:
  - a new `pipeline_runs` row exists
  - status is `succeeded`
  - `duration_ms` and `steps` are populated
