from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, text

from app.observability.run_tracking import RunTracker

pytestmark = pytest.mark.integration


class _NoopLogger:
    def info(self, _message: str, **_kwargs: Any) -> None:
        return None


class _NoopSession:
    def add(self, _obj: Any) -> None:
        return None

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    return "__SET_IN_.ENV__" in value


def _database_url_from_config(config: dict[str, str]) -> str | None:
    direct = config.get("DATABASE_URL") or config.get("DB_URL")
    if direct and not _is_placeholder(direct):
        return direct

    user = config.get("POSTGRES_USER")
    pwd = config.get("POSTGRES_PASSWORD")
    db = config.get("POSTGRES_DB")
    host = config.get("POSTGRES_HOST", "localhost")
    port = config.get("POSTGRES_PORT", "55432")

    if _is_placeholder(user) or _is_placeholder(pwd) or _is_placeholder(db):
        return None
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"


def _success_status_value() -> str:
    tracker = RunTracker(db=_NoopSession(), logger=_NoopLogger(), pipeline="status_probe")
    tracker.succeed()
    return tracker.row.status


def _failure_status_value() -> str:
    tracker = RunTracker(db=_NoopSession(), logger=_NoopLogger(), pipeline="status_probe")
    tracker.fail(RuntimeError("forced failure probe"))
    return tracker.row.status


def test_make_demo_creates_successful_pipeline_runs(tmp_path: Path) -> None:
    if shutil.which("make") is None:
        pytest.skip("`make` is required to run the demo path integration test.")

    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    if not dotenv_path.exists():
        pytest.skip("Missing .env; required by `make demo` and DB integration tests.")

    config = {**_parse_dotenv(dotenv_path), **os.environ}
    database_url = _database_url_from_config(config)
    if not database_url:
        pytest.skip(
            "Missing DATABASE_URL/DB_URL or POSTGRES_* config (or still using placeholder values)."
        )

    engine = create_engine(database_url, future=True)
    with engine.connect() as conn:
        table_exists = bool(conn.execute(text("SELECT to_regclass('pipeline_runs')")).scalar())
        if not table_exists:
            pytest.skip("pipeline_runs table not found. Run migrations (for example: make migrate).")

        before_started_at = conn.execute(text("SELECT max(started_at) FROM pipeline_runs")).scalar()

    env = os.environ.copy()
    env["FLAGS_REPORT_PATH"] = str(tmp_path / "flags_report.csv")

    proc = subprocess.run(
        ["make", "demo"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"`make demo` failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert proc.stdout.count("DEMO SUMMARY") == 1, proc.stdout

    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, pipeline, status, started_at
                    FROM pipeline_runs
                    WHERE pipeline IN ('ingest', 'flags')
                      AND (:before IS NULL OR started_at > :before)
                    ORDER BY started_at ASC
                    """
                ),
                {"before": before_started_at},
            )
            .mappings()
            .all()
        )

    assert rows, "Expected at least one new pipeline_runs row from `make demo`."

    expected_success = _success_status_value()
    bad_rows = [row for row in rows if row["status"] != expected_success]
    assert not bad_rows, (
        f"Expected all new demo rows to have status={expected_success!r}, got={bad_rows!r}"
    )


def test_make_demo_fail_returns_nonzero_and_persists_failed_run(tmp_path: Path) -> None:
    if shutil.which("make") is None:
        pytest.skip("`make` is required to run the demo path integration test.")

    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    if not dotenv_path.exists():
        pytest.skip("Missing .env; required by `make demo` and DB integration tests.")

    config = {**_parse_dotenv(dotenv_path), **os.environ}
    database_url = _database_url_from_config(config)
    if not database_url:
        pytest.skip(
            "Missing DATABASE_URL/DB_URL or POSTGRES_* config (or still using placeholder values)."
        )

    engine = create_engine(database_url, future=True)
    with engine.connect() as conn:
        table_exists = bool(conn.execute(text("SELECT to_regclass('pipeline_runs')")).scalar())
        if not table_exists:
            pytest.skip("pipeline_runs table not found. Run migrations (for example: make migrate).")

        before_started_at = conn.execute(text("SELECT max(started_at) FROM pipeline_runs")).scalar()

    env = os.environ.copy()
    env["DEMO_FAIL"] = "1"
    env["FLAGS_REPORT_PATH"] = str(tmp_path / "flags_report.csv")

    proc = subprocess.run(
        ["make", "demo"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0, "`make demo` should fail when DEMO_FAIL=1."
    assert proc.stdout.count("DEMO SUMMARY") == 1, proc.stdout

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT id, pipeline, status, error_summary
                    FROM pipeline_runs
                    WHERE pipeline = 'demo'
                      AND (:before IS NULL OR started_at > :before)
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ),
                {"before": before_started_at},
            )
            .mappings()
            .first()
        )

    assert row is not None, "Expected a failed demo row in pipeline_runs."
    assert row["status"] == _failure_status_value()
    assert row["error_summary"] is not None and "Forced demo failure" in row["error_summary"]
