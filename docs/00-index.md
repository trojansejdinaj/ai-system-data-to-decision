# Docs index

This folder contains documentation for the `ai-system-data-to-decision` portfolio repo.

## Start here
- Runbook: `docs/runbooks/local-dev.md`

## Architecture
- Week 01 system snapshot: `docs/architecture/01-system-snapshot.md`
- Week 04 DB persistence + dedupe: `docs/architecture/02-db-persistence-and-dedupe.md`
- Week 05 transform layer: `docs/architecture/03-transform-layer.md`
- Monthly metrics definitions: `docs/architecture/04-monthly-metrics.md`
- Week 06 dashboard v1: `docs/architecture/05-dashboard-v1.md`
- Week 08 reliability (run tracking + structured logs): `docs/architecture/06-reliability-run-tracking.md`
- Week 09 silver layer (clean.clean_records): `docs/architecture/07-silver-layer-clean-records.md`

## Runbooks
- Local dev workflow: `docs/runbooks/local-dev.md`
- Database: `docs/runbooks/database.md`
- Migrations: `docs/runbooks/migrations.md`
- Troubleshooting: `docs/runbooks/troubleshooting.md`

## Decisions (ADRs)
- 0001: uv + pyproject.toml: `docs/decisions/0001-uv-and-pyproject.md`
- 0002: Postgres port 55432: `docs/decisions/0002-db-port-55432.md`
- 0003: Secrets via .env + compose substitution: `docs/decisions/0003-secrets-and-env-substitution.md`
- 0004: DB readiness via healthcheck + wait: `docs/decisions/0004-db-readiness.md`
- 0005: Raw ingestion before normalization: `docs/decisions/0005-raw-ingestion-first.md`
- 0006: Cleaning + normalization module: `docs/decisions/0006-cleaning-and-normalization.md`
- 0007: DB persistence + idempotent upserts: `docs/decisions/0007-db-persistence-migrations-upsert.md`
- 0008: Transform layer + monthly metrics: `docs/decisions/0008-transform-layer-monthly-metrics.md`
- 0009: Dashboard v1 + summary tables: `docs/decisions/0009-dashboard-v1-summary-tables.md`
- 0010: Exceptions/flags v1: `docs/decisions/0010-exceptions-flags-v1.md`
- 0011: Reliability: run tracking + structured logs: `docs/decisions/0011-reliability-run-tracking.md`
- 0012: Silver layer + metrics refresh runner: `docs/decisions/0012-silver-layer-and-metrics-refresh.md`

## Changelog
- Week 01: `docs/changelog/week-01.md`
- Week 02: `docs/changelog/week-02.md`
- Week 03: `docs/changelog/week-03.md`
- Week 04: `docs/changelog/week-04.md`
- Week 05: `docs/changelog/week-05.md`
- Week 06: `docs/changelog/week-06.md`
- Week 07: `docs/changelog/week-07.md`
- Week 08: `docs/changelog/week-08.md`
- Week 09: `docs/changelog/week-09.md`

## Evidence
- Week 05: `docs/assets/week-05/`
- Week 06: `docs/assets/week-06/`
- Week 07: `docs/assets/week-07/`
- Week 08: `docs/assets/week-08/`
- Week 09: `docs/assets/week-09/`
