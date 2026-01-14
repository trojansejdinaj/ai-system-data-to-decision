# Dashboard v1 (monthly + trend)

## Purpose
Provide a fast, human-readable “60 second” view of what the system has ingested:
- latest monthly snapshot (headline numbers)
- monthly table (one row per month)
- trend table (bucketed series with a simple visual bar)

This dashboard is intentionally simple (HTML + server-rendered template) and is backed by DB summary tables for speed.

## Routes

UI:
- `GET /dashboard`
  - Renders an HTML page that calls the JSON endpoints below.

API:
- `GET /dashboard/monthly`
  - Optional filters:
    - `start` (date, inclusive) — filter by `month_start >= start`
    - `end` (date, exclusive) — filter by `month_start < end`
  - Source: `summary.monthly_metrics`

- `GET /dashboard/trend`
  - Required:
    - `start` (date, inclusive)
    - `end` (date, exclusive)
  - Optional:
    - `granularity`: `day | week | month` (default: `day`)
    - `metric`:
      - `total_records | distinct_records | distinct_source_ids | distinct_sources | distinct_categories`
      - default: `total_records`
  - Source: `summary.daily_metrics` (bucketed in query layer)

## Data sources

### Monthly snapshot
- Table: `summary.monthly_metrics`
- Time bucket:
  - `month_start = date_trunc('month', event_time)::date`

### Trend series
- Table: `summary.daily_metrics`
- Time bucket:
  - `day_date` (already bucketed; later buckets derived in query)

## Metric definitions
The dashboard uses the same metric definitions across daily + monthly tables:

- `total_records` = `COUNT(*)`
- `distinct_records` = `COUNT(DISTINCT (source, record_hash))`
  - Rationale: aligns with DB dedupe constraint on `(source, record_hash)`
- `distinct_source_ids` = `COUNT(DISTINCT source_id)`
- `distinct_sources` = `COUNT(DISTINCT source)`
- `distinct_categories` = `COUNT(DISTINCT category)`

## Operational notes
- The dashboard is only as good as the summary tables.
- If the dashboard loads but shows empty tables, ingest data and rebuild summaries.
- If `/dashboard/monthly` 500s with “AmbiguousParameter” when filters are omitted, ensure optional date params are CAST to date in the SQL query (typed NULL).

## Evidence
See `docs/assets/week-06/` for the screenshot pack.
