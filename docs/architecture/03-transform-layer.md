# Transform layer

## Purpose
The transform layer turns persisted data into decision-ready datasets.

In this project, the transform layer currently produces a **monthly metrics summary** using SQL that can be run repeatedly with deterministic results.

## Layers
- **raw**: `public.raw_records` (source-shaped with dedupe keys)
- **summary**: `summary.monthly_metrics` (monthly rollups)

A dedicated clean persistence layer can be added later; for now, metrics are derived from persisted raw records (post-dedupe).

## Transform artifacts
- SQL source of truth:
  - `src/app/transform/monthly_metrics.sql`
- Summary view:
  - `summary.monthly_metrics`
- Data quality checks log:
  - `summary.data_quality_checks`

## Reproducibility rules
- Month bucketing uses `event_time` (timestamptz) with:
  - `month_start = date_trunc('month', event_time)::date`
- Deduplication relies on unique `(source, record_hash)` in `public.raw_records`
- Metrics are recomputed from persisted rows (no manual spreadsheet edits)
