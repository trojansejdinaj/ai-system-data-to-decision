# Monthly metrics

## Purpose
Canonical monthly rollups used for reporting and later decision automation.

## Source
Input table:
- `public.raw_records`

Output:
- `summary.monthly_metrics` (view)

## Time bucketing
- `month_start = date_trunc('month', event_time)::date`

## Metric definitions
All metrics are computed per `month_start`:

- `total_records`
  - Definition: `COUNT(*)`
  - Meaning: number of persisted (deduped) raw records in that month

- `distinct_records`
  - Definition: `COUNT(DISTINCT record_hash)`
  - Meaning: unique records by stable hash; should match `total_records` once dedupe is enforced

- `distinct_source_ids`
  - Definition: `COUNT(DISTINCT source_id)`
  - Meaning: unique upstream identifiers seen in the month

- `distinct_sources`
  - Definition: `COUNT(DISTINCT source)`
  - Meaning: number of distinct sources contributing data in the month

- `distinct_categories`
  - Definition: `COUNT(DISTINCT category)`
  - Meaning: category diversity for that month

## Screenshot
- `docs/assets/week05/monthly-metrics-query.png`
