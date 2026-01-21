# Troubleshooting Runbook

Use this when local dev breaks. Goal: get back to green fast.

---

## Fast triage checklist

### 1) Is the API running?
```bash
curl -i http://localhost:8000/health
```

### 2) Is Postgres healthy?
```bash
docker compose ps
```

### 3) Are migrations applied?
```bash
make migrate
```

### 4) Are the pipelines healthy?
```bash
make demo
make clean
make metrics
make runs
```
Common failures + fixes
1) Address already in use (port 8000)
Cause

You started uvicorn twice (ex: make dev-all already runs the API, then you ran make run in another terminal).

Fix

Stop one of them (CTRL+C), then run just one server.

### 2) DATABASE_URL is required (flags/clean/metrics)

**Cause**

The CLI is running without environment exported.

**Fix**

```bash
set -a
source .env
set +a
```

Then:

```bash
make flags
make clean
make metrics
```

### 3) RunTracker.succeed() got an unexpected keyword argument 'meta'

**Cause**

`RunTracker.succeed()` does not accept `meta=...` (meta belongs on the row).

**Fix**

Update the pipeline to set `tracker.row.meta[...] = ...` then call `tracker.succeed()`.

### 4) Metrics runner fails: Textual SQL expression ... should be explicitly declared as text(...)

**Cause**

SQLAlchemy requires wrapping raw SQL strings.

**Fix**

In [src/app/transform/__main__.py](src/app/transform/__main__.py):

```python
from sqlalchemy import text

db.execute(text(stmt))
```

### 5) Metrics SQL fails: "monthly_metrics" is not a view

**Cause**

A previous version created `summary.monthly_metrics` as a TABLE or MATERIALIZED VIEW. `CREATE OR REPLACE VIEW` can't replace those.

**Fix**

In [src/app/transform/monthly_metrics.sql](src/app/transform/monthly_metrics.sql), drop all possible object types before creating the view:

```sql
DROP MATERIALIZED VIEW IF EXISTS summary.monthly_metrics;
DROP TABLE IF EXISTS summary.monthly_metrics;
DROP VIEW IF EXISTS summary.monthly_metrics;
```

Then:

```bash
make metrics
```

### 6) make metrics says SQL file missing / path issues

**Cause**

Redirecting `< path.sql` inside a container doesn't work if the file is only on host. The fix is to run a small Python wrapper (`python -m app.transform`) that reads the file from host and executes it.

**Fix**

Use the metrics runner module ([src/app/transform/__main__.py](src/app/transform/__main__.py)) and run:

```bash
make metrics
```

### 7) SQLAlchemy model error: MappedAnnotationError ... Python type object ... not resolvable

**Cause**

A model column type annotation is too generic (ex: `Mapped[object]`) or missing a SQLAlchemy type mapping.

**Fix**

Ensure mapped columns use concrete types (e.g. `Mapped[Decimal | None]` + proper SQLAlchemy column type).

## Nuke-from-orbit (last resort, dev only)

Wipes DB volume and starts fresh:

```bash
docker compose down -v
make dev-all
make demo
make clean
make metrics
make runs
```