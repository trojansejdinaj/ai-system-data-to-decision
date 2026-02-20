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


def test_decisions_pipeline_writes_run_and_decision_row() -> None:
    engine = _db_engine()

    if not _table_exists(engine, "pipeline_runs"):
        pytest.skip("pipeline_runs table not found. Did you run migrations (make migrate)?")
    if not _table_exists(engine, "decisions"):
        pytest.skip("decisions table not found. Did you run migrations (make migrate)?")

    with engine.connect() as conn:
        before = conn.execute(
            text(
                """
                SELECT started_at
                FROM pipeline_runs
                WHERE pipeline = 'decisions'
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
        [sys.executable, "-m", "app.decisions"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"decisions pipeline failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

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
                        d.policy_hash,
                        d.decision,
                        d.score,
                        d.reasons,
                        d.explanation_json,
                        d.created_at
                    FROM pipeline_runs pr
                    LEFT JOIN decisions d ON d.run_id = pr.id
                    WHERE pr.pipeline = 'decisions'
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

        assert row is not None, "Expected a new pipeline_runs row for pipeline='decisions'"
        assert row["status"] == "succeeded"
        assert row["decision_run_id"] == row["run_id"]

        assert row["policy_version"] == "v0"
        assert isinstance(row["policy_hash"], str) and len(row["policy_hash"]) == 64
        assert row["decision"] is not None
        assert row["score"] is not None
        assert row["created_at"] is not None
        assert isinstance(row["reasons"], list)
        assert isinstance(row["explanation_json"], dict)

        decision_count = conn.execute(
            text("SELECT COUNT(*) FROM decisions WHERE run_id = :run_id"),
            {"run_id": row["run_id"]},
        ).scalar_one()
        assert decision_count == 1
