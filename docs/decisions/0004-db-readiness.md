# 0004 - DB readiness: healthcheck + wait before migrations

## Status
Accepted

## Context
Running migrations immediately after starting Postgres can race startup and fail with connection errors.

## Decision
- Add Postgres `healthcheck` using `pg_isready`.
- Add `make db-wait` and make `migrate` depend on it.

## Consequences
- Migrations are reliable and repeatable.
- Slight delay on first boot; worth it.
