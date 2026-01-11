# Week 05 — Transform layer (monthly metrics)

## Goal
Build a reproducible transform layer producing monthly summary metrics from persisted data.

## What shipped
- Added transform layer SQL: `src/app/transform/monthly_metrics.sql`
- Created schema `summary`
- Created view `summary.monthly_metrics`
- Created table `summary.data_quality_checks` (for validation logging)
- Validated monthly totals against the source `public.raw_records`
- Captured metrics query screenshot

## Metrics (current)
Monthly metrics are computed from `public.raw_records` using:
- `month_start = date_trunc('month', event_time)::date`
- row volumes and distinct counts using `record_hash` and `source_id`

Example output after ingesting samples:
- `2026-01-01`: `total_records=10`, `distinct_records=10`, `distinct_source_ids=10`,
  `distinct_sources=1`, `distinct_categories=3`

## Verification
Commands:
- Ingest samples:
  - `POST /ingest/samples`
- Build metrics:
  - `make metrics`
- Inspect:
  - `SELECT * FROM summary.monthly_metrics ORDER BY month_start;`

## Evidence
- Screenshot: `docs/assets/week05/monthly-metrics-query.png`

## Next
- Add automated control-total checks (write rows into `summary.data_quality_checks`)
- Consider materializing metrics into a table once stable (performance + snapshotting)
