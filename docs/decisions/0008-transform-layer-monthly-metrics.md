# ADR 0008: Transform layer and monthly metrics

## Status
Accepted — 2026-01-11

## Context
We need reproducible monthly metrics derived from persisted data, with clear definitions and validation hooks.

## Decision
- Implement monthly metrics as SQL in `src/app/transform/monthly_metrics.sql`
- Materialize results under `summary.monthly_metrics`
  - Week 05: view (iteration)
  - Week 06: table (dashboard snapshot + predictable performance)
- Create a checks table to log validation outcomes:
  - `summary.data_quality_checks`
- Base metrics on persisted, deduped raw records:
  - `public.raw_records`

## Rationale
- SQL is auditable and easy to review.
- Starting with a view allows rapid iteration while metrics stabilize.
- Materializing into a table supports dashboard performance and stable snapshots.
- Dedupe is enforced at the database level via unique `(source, record_hash)`.
- The checks table enables future automated validation without changing the core metrics contract.

## Notes
Metric definitions are documented in `docs/architecture/04-monthly-metrics.md`.
