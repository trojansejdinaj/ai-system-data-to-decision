# Week 09 — Silver layer + tracked metrics refresh

## Shipped
- Silver layer pipeline: `make clean` builds/refreshes `clean.clean_records`
- Metrics refresh runner: `make metrics` executes SQL via `python -m app.transform`
- Monthly metrics updated to compute from silver (`clean.clean_records`) into `summary.monthly_metrics` (VIEW)
- Run tracking includes the `metrics` pipeline
- Makefile workflow improvements (demo flow, metrics execution stability)

## Proof
- `make clean` prints `Total clean records: 10` (sample)
- `make metrics` prints `summary.monthly_metrics` row
- `make runs` shows `clean` + `metrics` succeeded entries

## Notes
This week completes a minimal Bronze → Silver → Gold stack with run-tracking across pipelines.
