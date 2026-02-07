# Demo Runbook

This runbook explains how to run the **golden path demo** (`make demo`) and what to expect.

---

## Prerequisites

Before running `make demo`:

1. **Python 3.12+** installed
2. **uv** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Docker + Docker Compose** running
4. **Dependencies synced:** `make sync`
5. **.env file created:** `cp .env.example .env` and fill in `POSTGRES_PASSWORD` (at minimum)
6. **(Optional but recommended) direnv set up:**
   ```bash
   echo 'dotenv' > .envrc
   direnv allow
   ```

---

## Running make demo

One command:

```bash
make demo
```

This orchestrates the complete golden path end-to-end:

1. Starts Postgres (docker compose up -d)
2. Waits for DB readiness
3. Applies migrations (`uv run python -m alembic upgrade head`)
4. Runs the demo runner (`uv run python -m app.demo`)
5. Demo runner executes ingestion + flags
6. Prints one final `DEMO SUMMARY` block

**Expected final output block:**

```
============================================================
DEMO SUMMARY
------------------------------------------------------------
run_id      : 123e4567-e89b-12d3-a456-426614174000
status      : succeeded
duration_ms : 1538
records_in  : 30
records_out : 20
============================================================
```

Inspect persisted runs:

```bash
make runs
```

Exit code: **0** (success)

---

## Prove Idempotency: Run Twice

The real proof of idempotency is running the demo twice in a row:

```bash
make demo
make demo
```

**Expected on run #1:**
- Ingestion: `inserted_records: 20, deduped_records: 0` (fresh samples)
- Flags: runs and scans all 10 records
- `raw_records` count: 10

**Expected on run #2:**
- Ingestion: `inserted_records: 0, deduped_records: 20` (duplicate detection)
- Flags: runs again, sees same 10 records (no change)
- `raw_records` count: still 10 (not 20!)
- Both pipeline_runs appear in the summary query

**Why this proves idempotency:**
- Ingestion deduplicates: same 20 sample rows are recognized as duplicates on run #2
- No extra records inserted (data integrity)
- Flags is stateless: scans latest N rows, no side effects
- Safe to run repeatedly in CI/CD without polluting data

---

## Common Failures

### 1) "waiting for postgres..." loops forever

**Cause**

Docker container is not running or Postgres is not responding.

**Check:**

```bash
docker compose ps
```

If the `db` service is not `Up`, start it:

```bash
make db-up
docker compose logs db
```

If it started but is stuck, reset:

```bash
docker compose down -v
make db-up
```

Then retry:

```bash
make demo
```

### 2) "Failed to spawn: alembic (os error 2)"

**Cause**

Alembic binary not found on `$PATH`. Usually happens if `uv sync` was not run.

**Fix:**

```bash
uv sync
make demo
```

The `Makefile` uses `uv run python -m alembic`, not `alembic` directly, so the module must be installed.

### 3) "DATABASE_URL is required" (env vars missing)

**Cause**

Environment variables not loaded into the shell.

**Fix (preferred): direnv**

```bash
echo 'dotenv' > .envrc
direnv allow
```

Then in a fresh shell:

```bash
make demo
```

**Fix (fallback): manual env load**

```bash
set -a
source .env
set +a
make demo
```

### 4) Exit code non-zero but no clear error message

**Cause**

One of the intermediate steps failed silently. The Makefile uses `set -euo pipefail`, so any failure should be visible, but check the last few lines of output.

**Fix:**

Run the steps manually to isolate the issue:

```bash
make db-up
make migrate
make ingest-samples
make flags
make runs
```

Each command will show its error.

---

## Success Criteria

✅ **make demo passed** means:

- Postgres is healthy and migrated
- Ingestion ran without errors (raw_records populated)
- Flags engine ran without errors
- Pipeline runs are tracked in the DB
- Exit code is 0
- Success banner printed

You can now run this in CI/CD as a regression test, or demo it to stakeholders as proof the stack works end-to-end.

---

## Next

- Add `make demo` to GitHub Actions CI for automated regression checks
- Dashboard: add a "recent runs" widget to visualize pipeline_runs
- See [local-dev.md](./local-dev.md) for other commands (dev-all, run, clean, metrics, etc.)
