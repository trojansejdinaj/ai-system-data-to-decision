# 0011 — Reliability: run tracking + structured logs

## Status
Accepted

## Context
As the system grows (ingest → clean → transform → flags → dashboard), we need to:
- debug failures quickly with actionable context
- correlate all log lines belonging to a single run
- measure step performance over time
- provide auditable evidence (“this run succeeded/failed, here’s why”) in the database

Print-based logging and ad-hoc error handling do not scale once multiple pipelines exist.

## Decision
1) Use structured JSON logs for all pipeline execution events.
2) Introduce a generic run tracking table (`pipeline_runs`) to store:
   - run identity (`run_id`)
   - pipeline name
   - status (`running/succeeded/failed`)
   - timing (`started_at`, `ended_at`, `duration_ms`)
   - per-step results (JSON list with step name/status/duration)
   - error info on failures (`error_type`, `error_message`)
3) Implement a small `RunTracker` + `StepTimer` wrapper to:
   - create the DB row at run start
   - log step started/succeeded/failed with timing
   - mark the run succeeded/failed and persist error fields

## Why this approach
- JSON logs are machine-readable and easy to grep/filter.
- `run_id` makes correlation trivial across steps, pipelines, and tooling.
- DB run tracking provides a durable record independent of terminal logs.
- Storing `steps` as JSON keeps v1 simple while still supporting dashboards later.

## Alternatives considered
- **Plain text logs + grep**: hard to correlate; brittle; no stable schema.
- **Third-party logging libs (structlog/loguru)**: nice, but not necessary for Week 08.
- **Separate `run_steps` table**: more queryable, but increases schema complexity early.

## Consequences
- Small amount of boilerplate at pipeline entrypoints (wrap steps).
- Tests should validate:
  - unit: run tracker behavior without DB
  - integration: pipeline writes a `pipeline_runs` row

## Follow-ups
- Optional: add `run_steps` table if we need richer analytics.
- Optional: add a lightweight dashboard panel for recent runs and failures.
- Optional: emit counters (records processed) into `meta` or step metadata.
