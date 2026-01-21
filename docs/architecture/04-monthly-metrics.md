# Monthly Metrics (Gold)

## Output
- **View:** `summary.monthly_metrics`

## Input (source of truth)
- **Table:** `clean.clean_records` (Silver)

Gold metrics are computed from the **silver** layer (clean data), not directly from raw ingestion.

---

## What it contains
For each month (`month_start` derived from `event_time`), the view provides:

- `total_records`
- `distinct_records` (by `record_hash`)
- `distinct_source_ids`
- `distinct_sources`
- `distinct_categories`

> Note: because `clean.clean_records` is deduped by `(source, record_hash)`, totals may be lower than raw ingestion totals.

---

## Refresh mechanism (tracked)

A small runner applies the SQL file and records a pipeline run:

- SQL definition: [src/app/transform/monthly_metrics.sql](src/app/transform/monthly_metrics.sql)
- Runner: `python -m app.transform` (wired to `make metrics`)
- Run tracking: `pipeline_runs.pipeline = "metrics"`

**Run it:**

```bash
make metrics
```

**This ensures:**

- `summary` schema exists
- `summary.data_quality_checks` table exists (optional tracking)
- `summary.monthly_metrics` exists as a VIEW (recreated deterministically)

## Implementation notes

### Idempotency / object type safety

If `summary.monthly_metrics` ever existed as a TABLE or MATERIALIZED VIEW in older iterations, the SQL file should drop those before creating the VIEW, e.g.:

```sql
DROP MATERIALIZED VIEW IF EXISTS summary.monthly_metrics;
DROP TABLE IF EXISTS summary.monthly_metrics;
DROP VIEW IF EXISTS summary.monthly_metrics;
```

This prevents "monthly_metrics" is not a view errors when refreshing.

## Validation

### Inspect the gold output

```sql
SELECT * FROM summary.monthly_metrics ORDER BY month_start;
```

### Validate totals against silver

```sql
SELECT
  date_trunc('month', event_time)::date AS month_start,
  COUNT(*) AS clean_count
FROM clean.clean_records
WHERE event_time IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

**Expected (for sample data):**

- one month row
- `total_records = 10` (after clean upsert)

## Observability

After running `make metrics`, confirm a tracked run exists:

```bash
make runs
```

You should see a recent:

```
metrics | succeeded
```

with step details for `apply_sql`.