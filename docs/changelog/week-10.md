# Week 10 Changelog

## Shipped

- **make demo golden path wired end-to-end:** `make demo` now runs the complete stack: services up → migrate → ingest (samples via CLI) → flags → summary queries. Single command, no API dependency required. Meets T1 DoD.

- **demo is repeatable (idempotency proven by second run):** Run `make demo` twice back-to-back to see: `inserted_records: 0`, `deduped_records: 20`, `raw_records` stays at 10. Full deduplication proof.

- **migrations invocation hardened (module-based Alembic):** All Alembic commands now use `uv run python -m alembic` (not relying on `alembic` binary on `$PATH`). Fixes "Failed to spawn: alembic" errors. Updated Makefile targets: `migrate`, `revision`.

- **direnv .envrc added for auto env loading:** Set up `.envrc` with `dotenv` directive. Run `direnv allow` once, then env vars load automatically in the shell. Documented in local-dev.md and troubleshooting.md; `.envrc` safe to commit, `.env` stays gitignored.

## Documentation

- **0013 ADR: Demo as Golden Path** — rationale for why `make demo` is the canonical test, idempotency design, and observability via pipeline_runs.
- **Updated local-dev.md:** First-time setup now includes direnv option; portfolio demo flow reflects real golden path + idempotency test.
- **Updated troubleshooting.md:** New failure case "Failed to spawn: alembic"; improved DATABASE_URL section with direnv steps and fallback.
- **Updated migrations.md:** Reliability note on module-based Alembic invocation.

## Next

- Integrate golden-path demo into CI/CD (GitHub Actions) for automated regression checks.
- Dashboard v2: add run summaries widget.
