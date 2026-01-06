# Week 01 Changelog

**Status:** Foundation scaffold complete.  
**Date Range:** January 01–05, 2026

---

## Summary

Delivered a clean, production-ready foundation for the "data → decision" portfolio system. The focus was on building a solid base with correct tooling, architecture, and local dev workflow — not features.

---

## What Was Built

### Core Infrastructure

- **FastAPI app** with a `/health` endpoint for readiness checks
- **PostgreSQL 16** via Docker Compose with volume persistence
- **Alembic migrations** for schema management with SQLAlchemy ORM
- **Docker Compose** config with healthchecks + environment substitution
- **Make targets** for common tasks (sync, run, test, migrate, etc.)

### Developer Experience

- **Dependency management** via `uv` + `pyproject.toml` + `uv.lock`
- **Code quality** with ruff (lint + format)
- **Automated testing** with pytest
- **Auto-reload** FastAPI server during development
- **Database readiness** wait logic (no race conditions)

### Documentation & Decisions

- **ADRs (Architecture Decision Records)** for key choices:
  - 0001: Why uv + pyproject.toml (speed, reproducibility)
  - 0002: Why port 55432 for Postgres (avoid conflicts with host default)
  - 0003: Secrets via `.env` + Docker Compose substitution
  - 0004: DB readiness via healthcheck + wait-for-it script
- **Runbooks** for local dev, database, migrations, and troubleshooting
- **README** with quickstart and common commands

### Testing

- Health endpoint test in `tests/test_health.py`
- Pytest configured with proper discovery
- Ready for CI/CD integration

---

## Key Design Decisions

| Decision | Rationale | Record |
|----------|-----------|--------|
| `uv` for package management | Fast, reproducible, modern Python | [0001](../decisions/0001-uv-and-pyproject.md) |
| Postgres port 55432 | Avoid conflicts with default 5432 | [0002](../decisions/0002-db-port-55432.md) |
| `.env` + Docker Compose interpolation | Keep secrets local, not in code | [0003](../decisions/0003-secrets-and-env-substitution.md) |
| Healthcheck + db-wait | Prevent app startup race conditions | [0004](../decisions/0004-db-readiness.md) |

---

## File Structure

```
├── alembic.ini                      # Alembic config
├── docker-compose.yml               # Postgres + volumes
├── Makefile                         # Dev commands
├── pyproject.toml                   # Dependencies + config
├── pytest.ini                       # Test discovery
├── .env.example                     # Env template
├── src/
│   ├── app/
│   │   ├── main.py                  # FastAPI app (GET /health)
│   │   ├── core/
│   │   │   └── config.py            # Settings from .env
│   │   └── db/
│   │       ├── session.py           # SQLAlchemy SessionLocal
│   │       └── migrations/
│   │           ├── env.py           # Alembic env config
│   │           └── versions/
│   │               └── 78b15fee4f9b_init.py  # Initial migration
│   └── tests/
│       └── test_health.py           # Health endpoint test
└── docs/
    ├── 00-index.md                  # Docs index
    ├── decisions/                   # ADRs
    ├── runbooks/                    # Operational guides
    └── changelog/                   # This file
```

---

## Commands Available

| Command | Purpose |
|---------|---------|
| `make sync` | Install dependencies |
| `make run` | Start FastAPI server |
| `make test` | Run pytest |
| `make fmt` | Format code (ruff) |
| `make lint` | Lint + auto-fix (ruff) |
| `make db-up` | Start Postgres container |
| `make db-down` | Stop Postgres container |
| `make db-wait` | Wait for Postgres readiness |
| `make migrate` | Apply Alembic migrations |
| `make revision m="msg"` | Create new migration |
| `make logs` | Tail Docker logs |

---

## What's NOT Here (Yet)

No data pipeline, ETL, model training, or API endpoints beyond `/health`. This is intentional—a clean base to build on.

---

## Next Steps

### Immediate

1. Verify local setup: `make sync && make db-up && make run`
2. Test health endpoint: `curl http://localhost:8000/health`
3. Run migrations: `make migrate`
4. Run tests: `make test`

### Short Term

- Add domain models (SQLAlchemy ORM classes)
- Create API endpoints for core entities
- Write integration tests
- Add logging + monitoring

### Medium Term

- Data ingestion layer (ETL/ELT)
- Transformation pipelines
- Model training framework
- Decision serving APIs

---

## Notes

- All environment variables are sourced from `.env` (use `.env.example` as template)
- Postgres data persists in Docker volume `d2d_pg` across restarts
- Migrations are auto-applied on deployment
- No production secrets are committed to the repo

---

## References

- [Local Dev Runbook](../runbooks/local-dev.md)
- [Database Runbook](../runbooks/database.md)
- [Migrations Runbook](../runbooks/migrations.md)
- [Troubleshooting Runbook](../runbooks/troubleshooting.md)
- [ADRs](../decisions/)

---

**Status:** Foundation ready for Week 02 feature development.
