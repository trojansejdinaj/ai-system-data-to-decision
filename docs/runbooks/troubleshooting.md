# Troubleshooting Runbook

Use this when local dev breaks. The goal is to get you back to a working state fast.

---

## Fast triage checklist (do this first)

### 1) Is the API running?
```bash
curl -i http://localhost:8000/health
```

### 2) Is Postgres running and healthy?
```bash
docker compose ps
```

### 3) Do migrations match the DB?
```bash
uv run alembic current
```

### 4) Can the dashboard endpoints respond?
```bash
curl -i http://localhost:8000/dashboard/monthly
curl -i "http://localhost:8000/dashboard/trend?start=2025-12-15&end=2026-01-14"
```

### 5) Look at logs
- API logs: the terminal where uvicorn is running
- Docker logs:
```bash
make logs
```

---

## Database issues

### Problem: Postgres won’t accept connections
**Symptoms**
- `connection refused`
- `could not connect to server`
- `timeout`

**Fix**
```bash
make db-up
make db-wait
```

If it still fails:
```bash
docker compose ps
make logs
```

Destructive reset (wipes DB volume):
```bash
make db-reset
```

---

### Problem: `psql` command fails with role/user errors (e.g. role "root" does not exist)
**Cause**
- You ran `psql` without passing the correct user/db, so it defaulted to your shell user.

**Fix**
Use the container env values:
```bash
docker compose exec -T db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Or connect from host with explicit values:
```bash
psql -h localhost -p 55432 -U d2d_user -d d2d_db
```

---

## Migration issues

### Problem: Alembic says `head` but tables are missing
**Cause**
- A migration can be applied (version advances) even if its `upgrade()` did nothing (no-op or empty).

**Fix**
Force re-run by downgrading then upgrading:
```bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

Verify schema:
```bash
psql -h localhost -p 55432 -U d2d_user -d d2d_db -c "\dt summary.*"
```

---

### Problem: Downgrade fails because an object is a VIEW vs TABLE
**Symptoms**
- `WrongObjectType ... is not a table`
- hint says `Use DROP VIEW`

**Fix**
Make downgrade robust in migration code:
```sql
DROP VIEW IF EXISTS summary.monthly_metrics;
DROP TABLE IF EXISTS summary.monthly_metrics;
```

Then retry downgrade/upgrade.

---

## Import / module issues

### Problem: `ModuleNotFoundError: No module named 'app'`
**Cause**
- Repo uses `src/` layout and imports like `from app...`.
- If `src` isn’t on `PYTHONPATH`, `app` can’t be resolved.

**Fix**
Use Makefile targets (they set `PYTHONPATH=src`) or run manually:
```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload --env-file .env
```

---

### Problem: You accidentally used `scr` instead of `src`
**Symptoms**
- `ModuleNotFoundError: No module named 'scr'`

**Fix**
Use the correct module path:
- `uvicorn app.main:app` with `PYTHONPATH=src`
- (or) `uvicorn src.app.main:app` if you switch imports to `from src.app...`

---

## Dashboard issues

### Problem: `/dashboard` loads but `/dashboard/monthly` returns 500
**Common causes**
- Missing summary tables
- API connected to the wrong database
- SQL parameter typing errors

**Fix**
1) Confirm summary tables:
```bash
psql -h localhost -p 55432 -U d2d_user -d d2d_db -c "\dt summary.*"
```

2) Confirm API is loading `.env`:
- run via Makefile or with:
```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload --env-file .env
```

3) If error mentions `AmbiguousParameter`:
**Cause**
- Postgres can’t infer the type of NULL query params.

**Fix**
Cast optional params in SQL:
```sql
WHERE (CAST(:start AS date) IS NULL OR month_start >= CAST(:start AS date))
  AND (CAST(:end AS date) IS NULL OR month_start < CAST(:end AS date))
```

---

## “Nuke it from orbit” (last resort)

If you want a clean slate (dev only, wipes DB):
```bash
docker compose down -v
make dev-all
```

---

## Quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `role "root" does not exist` | wrong psql user | pass `-U` / use container `bash -lc` |
| `No module named app` | src not on PYTHONPATH | `PYTHONPATH=src ...` |
| `No module named scr` | typo | use `src` not `scr` |
| Alembic head but missing tables | no-op migration | downgrade/upgrade |
| Monthly endpoint 500 + AmbiguousParameter | NULL param typing | CAST params to date |
