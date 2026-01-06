# 0003 - Secrets via .env + Docker Compose env substitution

## Status
Accepted

## Context
We do not want secrets (DB password) committed into the repo. Docker Compose originally hardcoded the password.

## Decision
- `.env` holds real secrets locally (ignored by git).
- `.env.example` holds placeholders only (safe to commit).
- `docker-compose.yml` reads `POSTGRES_*` from environment substitution:
  - `${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}` to fail fast.

## Consequences
- Secrets stay local.
- First-time setup requires copying `.env.example` -> `.env` and setting password.
