# tests/test_pipeline_runs_integration.py
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def _build_database_url_from_env() -> str | None:
    """
    Build DATABASE_URL if the user didn't export it.
    Requires POSTGRES_* vars (especially POSTGRES_PASSWORD).
    """
    user = os.getenv("POSTGRES_USER")
    pwd = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "55432")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not (user and pwd and db):
        return None

    # SQLAlchemy URL for psycopg v3 driver
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"


def _db_engine():
    database_url = (
        os.getenv("DATABASE_URL") or os.getenv("DB_URL") or _build_database_url_from_env()
    )
    if not database_url:
        pytest.skip(
            "No DATABASE_URL/DB_URL and missing POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB; "
            "export env or load .env before running integration tests."
        )
    return create_engine(database_url, future=True)


def _table_exists(engine, table_name: str) -> bool:
    # checks current schema search_path
    q = text("SELECT to_regclass(:tname) IS NOT NULL AS exists")
    with engine.connect() as conn:
        return bool(conn.execute(q, {"tname": table_name}).scalar())


def test_flags_writes_pipeline_run_row(tmp_path):
    engine = _db_engine()

    # Your Week 08 migration should create this table.
    if not _table_exists(engine, "pipeline_runs"):
        pytest.skip("pipeline_runs table not found. Did you run migrations (make migrate)?")

    # Capture baseline: latest started_at for flags runs (could be NULL if none)
    with engine.connect() as conn:
        before = conn.execute(
            text(
                """
                SELECT started_at
                FROM pipeline_runs
                WHERE pipeline = 'flags'
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
        ).scalar()

    # Run the real pipeline via module entrypoint.
    # We force output into tmp_path to avoid touching docs/assets.
    env = os.environ.copy()
    env.setdefault(
        "DATABASE_URL",
        os.getenv("DATABASE_URL") or os.getenv("DB_URL") or _build_database_url_from_env() or "",
    )
    env["FLAGS_LIMIT"] = "10"
    env["FLAGS_REPORT_PATH"] = str(tmp_path / "flags_report.csv")

    proc = subprocess.run(
        [sys.executable, "-m", "app.flags"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"flags pipeline failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    # Fetch the newest flags run row created after `before`
    with engine.connect() as conn:
        row: dict[str, Any] | None = (
            conn.execute(
                text(
                    """
                SELECT pipeline, status, duration_ms, steps, error_type, error_message, started_at
                FROM pipeline_runs
                WHERE pipeline = 'flags'
                AND (:before IS NULL OR started_at > :before)
                ORDER BY started_at DESC
                LIMIT 1
                """
                ),
                {"before": before},
            )
            .mappings()
            .first()
        )

    assert row is not None, "Expected a new pipeline_runs row for pipeline='flags'"

    assert row["status"] == "succeeded", (
        f"Expected succeeded, got: {row['status']} ({row.get('error_message')})"
    )
    assert row["duration_ms"] is not None and row["duration_ms"] >= 0

    steps = row["steps"]
    assert isinstance(steps, list) and len(steps) > 0, "Expected non-empty steps JSON"

    # Minimal step shape guarantees (Week 08 contract)
    for s in steps:
        assert "step" in s and isinstance(s["step"], str)
        assert "status" in s and s["status"] in ("ok", "failed")
        assert "duration_ms" in s and isinstance(s["duration_ms"], int)

    # Should not have error fields on success
    assert row["error_type"] is None
    assert row["error_message"] is None
