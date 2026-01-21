/* ============================================================================
monthly_metrics.sql

Week 05+ update:
  Reproducible monthly metrics using SILVER (clean) layer as source of truth.

Inputs:
  - clean.clean_records   (silver)

Outputs:
  - summary.monthly_metrics (view)
  - summary.data_quality_checks (table)  [optional but recommended]

Notes:
  - Month bucket uses event_time (timestamptz) in clean_records
  - clean.clean_records may be deduped by (source, record_hash)
============================================================================ */

-- 0) Schemas
CREATE SCHEMA IF NOT EXISTS summary;

-- 1) Drop any existing monthly_metrics object safely (table/view/matview)
DO $$
DECLARE
  kind char;
BEGIN
  SELECT c.relkind
    INTO kind
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'summary'
    AND c.relname = 'monthly_metrics';

  IF kind IS NULL THEN
    -- nothing to drop
    RETURN;
  ELSIF kind = 'r' THEN
    EXECUTE 'DROP TABLE summary.monthly_metrics';
  ELSIF kind = 'v' THEN
    EXECUTE 'DROP VIEW summary.monthly_metrics';
  ELSIF kind = 'm' THEN
    EXECUTE 'DROP MATERIALIZED VIEW summary.monthly_metrics';
  ELSE
    RAISE NOTICE 'summary.monthly_metrics exists with relkind=% (not dropped)', kind;
  END IF;
END $$;

-- 2) Monthly metrics view (clean → summary)
CREATE OR REPLACE VIEW summary.monthly_metrics AS
WITH base AS (
  SELECT
    date_trunc('month', event_time)::date AS month_start,
    source,
    category,
    source_id,
    record_hash,
    value_decimal
  FROM clean.clean_records
  WHERE event_time IS NOT NULL
)
SELECT
  month_start,

  -- volumes
  COUNT(*) AS total_records,
  COUNT(DISTINCT record_hash) AS distinct_records,   -- stable dedupe key
  COUNT(DISTINCT source_id)   AS distinct_source_ids,

  -- basic dimensions
  COUNT(DISTINCT source)      AS distinct_sources,
  COUNT(DISTINCT category)    AS distinct_categories

  -- you can add numeric rollups later once "value" is typed/cleaned
FROM base
GROUP BY 1
ORDER BY 1;

-- 3) Data quality checks table (stores pass/fail results over time)
CREATE TABLE IF NOT EXISTS summary.data_quality_checks (
  id bigserial PRIMARY KEY,
  check_name text NOT NULL,
  check_scope text NOT NULL,          -- e.g. 'monthly_metrics'
  month_start date NULL,              -- optional per-month checks
  status text NOT NULL,               -- 'pass' | 'fail' | 'warn'
  expected bigint NULL,
  observed bigint NULL,
  details jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 4) Validation queries (run manually; copy/paste as needed)

-- A) Inspect the monthly metrics
-- SELECT * FROM summary.monthly_metrics ORDER BY month_start;

-- B) Control totals directly from clean_records (should match view totals)
-- SELECT
--   date_trunc('month', event_time)::date AS month_start,
--   COUNT(*) AS clean_count
-- FROM clean.clean_records
-- WHERE event_time IS NOT NULL
-- GROUP BY 1
-- ORDER BY 1;

-- C) Compare (diff should be 0)
-- SELECT
--   s.month_start,
--   s.total_records AS summary_count,
--   c.clean_count,
--   (s.total_records - c.clean_count) AS diff
-- FROM summary.monthly_metrics s
-- JOIN (
--   SELECT date_trunc('month', event_time)::date AS month_start,
--          COUNT(*) AS clean_count
--   FROM clean.clean_records
--   WHERE event_time IS NOT NULL
--   GROUP BY 1
-- ) c USING (month_start)
-- ORDER BY s.month_start;
