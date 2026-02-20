from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def _build_database_url_from_env() -> str | None:
    user = os.getenv("POSTGRES_USER")
    pwd = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "55432")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not (user and pwd and db):
        return None

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
    query = text("SELECT to_regclass(:table_name) IS NOT NULL")
    with engine.connect() as conn:
        return bool(conn.execute(query, {"table_name": table_name}).scalar())


def _column_exists(engine, table_name: str, column_name: str) -> bool:
    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
          AND column_name = :column_name
        LIMIT 1
        """
    )
    with engine.connect() as conn:
        return (
            conn.execute(query, {"table_name": table_name, "column_name": column_name}).first()
            is not None
        )


def test_decisions_pipeline_writes_run_and_decision_row() -> None:
    engine = _db_engine()

    if not _table_exists(engine, "pipeline_runs"):
        pytest.skip("pipeline_runs table not found. Did you run migrations (make migrate)?")
    if not _table_exists(engine, "decisions"):
        pytest.skip("decisions table not found. Did you run migrations (make migrate)?")
    if not _column_exists(engine, "decisions", "top_reason"):
        pytest.skip(
            "decisions.top_reason column not found. Did you run latest migrations (make migrate)?"
        )

    with engine.connect() as conn:
        before = conn.execute(
            text(
                """
                SELECT started_at
                FROM pipeline_runs
                WHERE pipeline = 'decision'
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
        ).scalar()

    env = os.environ.copy()
    env.setdefault(
        "DATABASE_URL",
        os.getenv("DATABASE_URL") or os.getenv("DB_URL") or _build_database_url_from_env() or "",
    )

    proc = subprocess.run(
        [sys.executable, "-m", "app.decision"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"decision pipeline failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert "DECISION:" in proc.stdout

    with engine.connect() as conn:
        row: dict[str, Any] | None = (
            conn.execute(
                text(
                    """
                    SELECT
                        pr.id AS run_id,
                        pr.status,
                        d.run_id AS decision_run_id,
                        d.policy_version,
                        d.decision,
                        d.score,
                        d.top_reason,
                        d.reasons,
                        d.created_at
                    FROM pipeline_runs pr
                    LEFT JOIN decisions d ON d.run_id = pr.id
                    WHERE pr.pipeline = 'decision'
                      AND (
                        CAST(:before AS timestamptz) IS NULL
                        OR pr.started_at > CAST(:before AS timestamptz)
                      )
                    ORDER BY pr.started_at DESC
                    LIMIT 1
                    """
                ),
                {"before": before},
            )
            .mappings()
            .first()
        )

        assert row is not None, "Expected a new pipeline_runs row for pipeline='decision'"
        assert row["status"] == "succeeded"
        assert row["decision_run_id"] == row["run_id"]

        assert row["policy_version"] == "v1"
        assert row["decision"] is not None
        assert row["score"] is not None
        assert row["top_reason"] is not None
        assert row["created_at"] is not None
        assert isinstance(row["reasons"], list)

        decision_count = conn.execute(
            text("SELECT COUNT(*) FROM decisions WHERE run_id = :run_id"),
            {"run_id": row["run_id"]},
        ).scalar_one()
        assert decision_count == 1
