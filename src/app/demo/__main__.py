from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence

from sqlalchemy import text

from app.db.session import SessionLocal
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

SUMMARY_WIDTH = 60


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _run_python_module(module: str, args: Sequence[str] = ()) -> None:
    cmd = [sys.executable, "-m", module, *args]
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{module} exited with code {proc.returncode}")


def _collect_subpipeline_counts(db, since_started_at) -> tuple[int, int]:
    row = (
        db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(records_in), 0) AS records_in,
                    COALESCE(SUM(records_out), 0) AS records_out
                FROM pipeline_runs
                WHERE pipeline IN ('ingest', 'flags')
                  AND started_at >= :since_started_at
                """
            ),
            {"since_started_at": since_started_at},
        )
        .mappings()
        .one()
    )
    return int(row["records_in"]), int(row["records_out"])


def format_demo_summary(
    *,
    run_id: str,
    status: str,
    duration_ms: int | None,
    records_in: int | None,
    records_out: int | None,
) -> str:
    pairs = [
        ("run_id", run_id),
        ("status", status),
        ("duration_ms", str(duration_ms if duration_ms is not None else "-")),
        ("records_in", str(records_in if records_in is not None else "-")),
        ("records_out", str(records_out if records_out is not None else "-")),
    ]
    key_width = max(len(key) for key, _ in pairs)

    lines = ["=" * SUMMARY_WIDTH, "DEMO SUMMARY", "-" * SUMMARY_WIDTH]
    for key, value in pairs:
        lines.append(f"{key:<{key_width}} : {value}")
    lines.append("=" * SUMMARY_WIDTH)
    return "\n".join(lines)


def main() -> int:
    logger = get_logger(__name__)
    db = SessionLocal()
    tracker = RunTracker(db, logger, pipeline="demo", input_ref="make demo")

    exit_code = 0

    try:
        with tracker.step("ingest_samples"):
            _run_python_module("app.ingestion", ["--samples"])

        if _is_truthy(os.getenv("DEMO_FAIL")):
            raise RuntimeError("Forced demo failure (DEMO_FAIL=1).")

        with tracker.step("flags"):
            _run_python_module("app.flags")

        records_in, records_out = _collect_subpipeline_counts(db, tracker.started_at)
        tracker.succeed(records_in=records_in, records_out=records_out)

    except Exception as exc:
        exit_code = 1
        records_in, records_out = _collect_subpipeline_counts(db, tracker.started_at)
        tracker.fail(exc, records_in=records_in, records_out=records_out)

    finally:
        print(
            format_demo_summary(
                run_id=str(tracker.run_id),
                status=str(tracker.row.status),
                duration_ms=tracker.row.duration_ms,
                records_in=tracker.row.records_in,
                records_out=tracker.row.records_out,
            )
        )
        db.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
