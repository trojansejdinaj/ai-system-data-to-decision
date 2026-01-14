# ADR 0009: Dashboard v1 and summary tables

## Status
Accepted — 2026-01-14

## Context
We need a minimal dashboard that provides a readable “monthly snapshot + trend” in under 60 seconds.
The dashboard should be DB-backed and fast, without expensive aggregation queries on every page load.

Week 05 introduced a monthly metrics *view* to iterate quickly, but a view can become expensive as data grows and is less predictable for a UI that should feel instantaneous.

## Decision
- Ship a simple server-hosted dashboard UI at:
  - `GET /dashboard`
- Expose DB-backed JSON endpoints:
  - `GET /dashboard/monthly` (optional `start`, `end`)
  - `GET /dashboard/trend` (required `start`, `end`; optional `granularity`, `metric`)
- Materialize summary metrics into tables for predictable read performance:
  - `summary.daily_metrics` (powers trend)
  - `summary.monthly_metrics` (powers monthly table + latest-month card)
- Standardize metric definitions across daily/monthly:
  - `distinct_records = COUNT(DISTINCT (source, record_hash))` to match dedupe constraint
- Provide a screenshot evidence pack under `docs/assets/week-06/`.

## Rationale
- Dashboards must be fast and predictable; pre-aggregated tables avoid repeated heavy queries.
- A thin UI + JSON endpoints keeps the system inspectable and testable (curl-able).
- Using the same metric names across daily/monthly simplifies interpretation and future automation.

## Consequences
- We now need a recompute/backfill story as data grows (periodic refresh or on-demand).
- Schema changes to raw records must preserve the metrics contract (or version the metrics).
- Optional filter parameters must be typed/cast in SQL to avoid NULL ambiguity in Postgres.

## Follow-ups
- Add automated control-total checks writing into `summary.data_quality_checks`.
- Add a small “insights” block (delta vs previous period + top category changes).
- Consider an export endpoint for snapshot JSON + screenshot pack generation (Playwright) once the UI stabilizes.
