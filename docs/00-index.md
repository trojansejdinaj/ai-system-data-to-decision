# Docs index

This folder contains documentation for the `ai-system-data-to-decision` portfolio repo.

## Start here
- Runbook: `docs/runbooks/local-dev.md`

## Architecture
- Week 01 system snapshot: `docs/architecture/01-system-snapshot.md`
- Week 04 DB persistence + dedupe: `docs/architecture/02-db-persistence-and-dedupe.md`

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

## Changelog
- Week 01: `docs/changelog/week-01.md`
- Week 02: `docs/changelog/week-02.md`
- Week 03: `docs/changelog/week-03.md`
- Week 04: `docs/changelog/week-04.md`
