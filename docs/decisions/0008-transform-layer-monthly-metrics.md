# ADR 0008: Transform layer and monthly metrics

## Status
Accepted — 2026-01-11

## Context
We need reproducible monthly metrics derived from persisted data, with clear definitions and validation hooks.

## Decision
- Implement monthly metrics as SQL in `src/app/transform/monthly_metrics.sql`
- Materialize results as a view:
  - `summary.monthly_metrics`
- Create a checks table to log validation outcomes:
  - `summary.data_quality_checks`
- Base metrics on persisted, deduped raw records:
  - `public.raw_records`

## Rationale
- SQL is auditable and easy to review.
- A view allows rapid iteration while metrics stabilize.
- Dedupe is enforced at the database level via unique `(source, record_hash)`.
- The checks table enables future automated validation without changing the metric view.

## Consequences
- Metrics are consistent and reproducible for a given DB state.
- Numeric aggregations over `value` are deferred until a typed clean layer is introduced.
- We can later switch from view → table if performance or snapshotting becomes necessary.
