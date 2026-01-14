# Monthly metrics

## Purpose
Canonical monthly rollups used for reporting and later decision automation.

## Source
Input table:
- `public.raw_records`

Output:
- `summary.monthly_metrics` (**table**)

> Week 05 started with a view for iteration; Week 06 materialized into a table to support a stable dashboard snapshot and predictable performance.

## Time bucketing
- `month_start = date_trunc('month', event_time)::date`

## Metric definitions
All metrics are computed per `month_start`:

- `total_records`
  - Definition: `COUNT(*)`
  - Meaning: number of persisted raw records in that month

- `distinct_records`
  - Definition: `COUNT(DISTINCT (source, record_hash))`
  - Meaning: unique records by stable hash **within a source**; matches the DB dedupe constraint on `(source, record_hash)`

- `distinct_source_ids`
  - Definition: `COUNT(DISTINCT source_id)`
  - Meaning: unique upstream identifiers observed

- `distinct_sources`
  - Definition: `COUNT(DISTINCT source)`
  - Meaning: number of distinct ingestion sources contributing data

- `distinct_categories`
  - Definition: `COUNT(DISTINCT category)`
  - Meaning: number of distinct categories observed

## Relationship to daily metrics
Daily rollups follow the same definitions and power the trend chart:
- `summary.daily_metrics` (table)

Monthly metrics are derived from `raw_records` directly (not from daily) to keep the definition unambiguous.

## Indexing
Primary key:
- `month_start`

Recommended index:
- `month_start` (for ordered reads and range filters)

## Notes
- These metrics are intended as *control totals* and simple dashboard KPIs, not as a full analytics model.
- If the pipeline later introduces “soft deletes” or late-arriving updates, consider recomputing monthly snapshots and recording validation checks in `summary.data_quality_checks`.
