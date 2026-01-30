# 0013 — Demo as Golden Path (T1 DoD)

## Status
Accepted

## Context

We needed a single, repeatable command that:
- Proves the entire stack works end-to-end
- Requires no manual steps or external dependencies (like running the API separately)
- Can be run multiple times to demonstrate idempotency
- Serves as a regression check for the whole pipeline

Previously, "demo" was a loose collection of separate curl/CLI commands that required the API to be running separately and were hard to orchestrate reliably.

## Decision

`make demo` is now the **canonical golden path**:

1. **Starts services:** `make db-up` (postgres container)
2. **Applies schema:** `make migrate` (via `uv run python -m alembic upgrade head`)
3. **Runs ingestion (CLI):** `make ingest-samples` (via `uv run python -m app.ingestion --samples`)
4. **Runs flags engine:** `make flags` (via `uv run python -m app.flags`)
5. **Prints summaries:**
   - Recent pipeline_runs (last 5)
   - Record counts (raw_records, ingest_runs)
6. **Exits with success banner** (exit 0)

**Key design choices:**
- Uses CLI-based ingestion, not the API (`/ingest/samples` endpoint)
- Sets `set -euo pipefail` to fail fast and exit non-zero on any error
- Repeatable: ingestion dedupes, flags reads latest N rows (no API state pollution)
- Captures all output inline (no separate log files to chase)

## Consequences

**Benefits:**
- Faster onboarding: new dev runs `make demo` and sees the entire stack work
- Reproducible demos: can run 2+ times in sequence to prove idempotency
- Regression test: if `make demo` fails, something broke
- No API dependency: simplifies local dev (one fewer process to manage)

**Trade-offs:**
- Slightly more Makefile logic (coordination of 5+ steps)
- Must use `@set -euo pipefail` to ensure failures propagate (not just silent hangs)
- Output is inline; no separate log artefacts

**Observability:**
- Run tracking is built in: each step logs a pipeline_run with metadata
- Second run shows deduplication: `inserted_records: 0`, `deduped_records: 20`
- Record counts prove idempotency: `raw_records` stays at 10 across runs
