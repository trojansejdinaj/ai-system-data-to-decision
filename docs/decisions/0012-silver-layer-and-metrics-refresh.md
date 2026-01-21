
---

## 7) `docs/decisions/0012-silver-layer-and-metrics-refresh.md` (NEW)

```md
# 0012 — Add Silver Layer + Trackable Metrics Refresh

## Status
Accepted

## Context
We had:
- ingestion into `public.raw_records` (bronze)
- monthly metrics logic (gold) but it was drifting and not consistently reproducible
- run tracking existed, but transforms were not tracked as pipeline runs

## Decision
1) Treat `clean.clean_records` as the **silver** source of truth for metrics.
2) Compute `summary.monthly_metrics` from `clean.clean_records`.
3) Implement a small metrics runner (`python -m app.transform`) so refresh is:
   - reproducible
   - tracked in `pipeline_runs`
   - not dependent on container file-path redirections

## Consequences
- The dashboard and metrics are now grounded on the clean layer.
- Transforms are observable: `make runs` shows metrics executions.
- The SQL for metrics is still the contract, but executed via a tracked runner.
