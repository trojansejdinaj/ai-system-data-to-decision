# Week 06 — Dashboard v1 (monthly + trend)

## Goal
Ship a minimal dashboard that a stranger can interpret in **60 seconds**:
- monthly snapshot (table + “latest month” card)
- trend view (bucketed counts with basic filters)
- evidence screenshot pack

## What shipped
- Dashboard UI page:
  - `GET /dashboard` (HTML)
- DB-backed API endpoints:
  - `GET /dashboard/monthly` (optional `start`, `end`)
  - `GET /dashboard/trend` (required `start`, `end`; optional `granularity`, `metric`)
- Summary tables for fast reads:
  - `summary.daily_metrics` (daily rollups; powers trend)
  - `summary.monthly_metrics` (monthly rollups; powers monthly table + latest-month card)
- Correct distinct-record definition aligned to dedupe constraint:
  - `distinct_records = COUNT(DISTINCT (source, record_hash))`
- Dev workflow improvement:
  - `make dev-all` brings up DB, runs migrations, and starts the API
  - `make run` uses `PYTHONPATH=src` so `from app...` imports resolve consistently

## Verification
Commands:
- Start everything:
  - `make dev-all`
- Dashboard:
  - UI: `http://localhost:8000/dashboard`
  - Monthly JSON: `curl -s http://localhost:8000/dashboard/monthly`
  - Trend JSON:
    - `curl -s "http://localhost:8000/dashboard/trend?start=2025-12-15&end=2026-01-14&granularity=day&metric=total_records"`
- DB sanity:
  - `\dt summary.*`
  - `SELECT * FROM summary.monthly_metrics ORDER BY month_start;`
  - `SELECT * FROM summary.daily_metrics ORDER BY day_date;`

## Evidence
Screenshot pack:
- `docs/assets/week-06/01-dashboard-default.png`
- `docs/assets/week-06/02-monthly-summary.png`
- `docs/assets/week-06/03-trend-default.png`
- `docs/assets/week-06/04-trend-filtered.png`

## Next
- Add a lightweight “insights” block (delta vs prior month + top category changes).
- Add a simple export endpoint for the screenshot pack / JSON snapshots.
- Add automated checks that compare summary tables vs source control totals and write to `summary.data_quality_checks`.
