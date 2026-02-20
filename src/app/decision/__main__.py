from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from app.db.models import Decision
from app.db.session import SessionLocal
from app.decision_policy import make_decision_summary
from app.flags.engine import flag_records
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

DEFAULT_QUERY = """
SELECT
  id,
  run_id,
  row_num,
  source,
  source_id,
  category,
  event_time,
  value,
  record_hash,
  ingested_at
FROM public.raw_records
ORDER BY ingested_at DESC
LIMIT :limit
"""


def main() -> int:
    limit = int(os.getenv("DECISION_LIMIT", "5000"))
    logger = get_logger(__name__)
    db = SessionLocal()
    tracker = RunTracker(db, logger, pipeline="decision", input_ref=f"raw_records(limit={limit})")

    records: list[dict] = []

    try:
        with tracker.step("load_inputs", meta={"limit": limit}):
            rows = db.execute(text(DEFAULT_QUERY), {"limit": limit}).mappings().all()
            records = [dict(row) for row in rows]
            tracker.log("inputs_loaded", total_records=len(records))

        with tracker.step("score", meta={"total_records": len(records)}):
            flagged_records = flag_records(records, now=datetime.now(UTC))
            summary = make_decision_summary(flagged_records, meta={"total_records": len(records)})
            tracker.log(
                "decision_scored",
                policy_version=summary.policy_version,
                decision=summary.decision,
                score=summary.score,
                top_reason=summary.top_reason,
            )

        with tracker.step("persist_decision"):
            decision_row = Decision(
                id=uuid.uuid4(),
                run_id=tracker.row.id,
                policy_version=summary.policy_version,
                decision=summary.decision,
                score=summary.score,
                top_reason=summary.top_reason,
                reasons=list(summary.reasons),
            )
            db.add(decision_row)
            db.flush()

        tracker.succeed(
            records_in=len(records),
            records_out=1,
            meta={
                "decision": summary.decision,
                "score": summary.score,
                "top_reason": summary.top_reason,
                "policy_version": summary.policy_version,
            },
        )

        print(
            f"DECISION: {summary.decision} | SCORE: {summary.score} | "
            f"TOP_REASON: {summary.top_reason}"
        )
        return 0

    except Exception as exc:
        tracker.fail(exc, records_in=len(records) or None, records_out=0)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
