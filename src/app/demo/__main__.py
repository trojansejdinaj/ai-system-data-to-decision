from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Sequence

from sqlalchemy import text

from app.db.session import SessionLocal
from app.features.compute import compute_features_for_run
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

SUMMARY_WIDTH = 60
DECISION_LINE_RE = re.compile(
    r"DECISION:\s*(?P<decision>[a-z]+)\s*\|\s*SCORE:\s*(?P<score>\d+)\s*\|\s*TOP_REASON:\s*(?P<top_reason>.+)"
)


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _run_python_module(module: str, args: Sequence[str] = ()) -> None:
    cmd = [sys.executable, "-m", module, *args]
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{module} exited with code {proc.returncode}")


def _run_decision_pipeline() -> dict[str, str | int]:
    cmd = [sys.executable, "-m", "app.decision"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "app.decision exited with code "
            f"{proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    parsed = _parse_decision_summary(proc.stdout)
    if parsed is None:
        raise RuntimeError("app.decision did not emit a parsable decision summary line.")
    return parsed


def _parse_decision_summary(stdout: str) -> dict[str, str | int] | None:
    matches = DECISION_LINE_RE.findall(stdout)
    if not matches:
        return None

    decision, score, top_reason = matches[-1]
    return {
        "decision": decision,
        "score": int(score),
        "top_reason": top_reason.strip(),
    }


def _collect_subpipeline_counts(db, since_started_at) -> tuple[int, int]:
    row = (
        db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(records_in), 0) AS records_in,
                    COALESCE(SUM(records_out), 0) AS records_out
                FROM pipeline_runs
                WHERE pipeline IN ('ingest', 'clean', 'flags', 'decision')
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
    decision: str | None,
    score: int | None,
    top_reason: str | None,
) -> str:
    pairs = [
        ("run_id", run_id),
        ("status", status),
        ("duration_ms", str(duration_ms if duration_ms is not None else "-")),
        ("records_in", str(records_in if records_in is not None else "-")),
        ("records_out", str(records_out if records_out is not None else "-")),
        ("decision", decision or "-"),
        ("score", str(score if score is not None else "-")),
        ("top_reason", top_reason or "-"),
    ]
    key_width = max(len(key) for key, _ in pairs)

    lines = ["=" * SUMMARY_WIDTH, "DEMO SUMMARY", "-" * SUMMARY_WIDTH]
    for key, value in pairs:
        lines.append(f"{key:<{key_width}} : {value}")
    lines.append("=" * SUMMARY_WIDTH)
    return "\n".join(lines)


def main() -> int:
    logger = get_logger(__name__)
    dataset_key = os.getenv("DEMO_SOURCE", "samples")
    db = SessionLocal()
    tracker = RunTracker(db, logger, pipeline="demo", input_ref="make demo")

    exit_code = 0
    decision_summary: dict[str, str | int] = {}

    try:
        with tracker.step("ingest_samples"):
            _run_python_module("app.ingestion", ["--samples", "--source", dataset_key])

        with tracker.step("clean"):
            _run_python_module("app.cleaning")

        if _is_truthy(os.getenv("DEMO_FAIL")):
            raise RuntimeError("Forced demo failure (DEMO_FAIL=1).")

        with tracker.step("flags"):
            _run_python_module("app.flags")

        with tracker.step("decision"):
            decision_summary = _run_decision_pipeline()

        with tracker.step("compute_features", meta={"dataset_key": dataset_key}):
            persisted = compute_features_for_run(db, tracker.run_id, dataset_key=dataset_key)
            tracker.log("features_persisted", feature_count=len(persisted), dataset_key=dataset_key)

        records_in, records_out = _collect_subpipeline_counts(db, tracker.started_at)
        tracker.succeed(
            records_in=records_in,
            records_out=records_out,
            meta=decision_summary,
        )

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
                decision=str(decision_summary.get("decision", "")) or None,
                score=(int(decision_summary["score"]) if "score" in decision_summary else None),
                top_reason=str(decision_summary.get("top_reason", "")) or None,
            )
        )
        db.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
