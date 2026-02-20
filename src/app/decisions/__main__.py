from __future__ import annotations

import json
import os
from typing import Any

from app.db.session import SessionLocal
from app.decisions.policy_v0 import evaluate
from app.decisions.service import save_decision_output, write_decision
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

DEFAULT_FEATURES: dict[str, float] = {
    "total_clean_records": 4.0,
    "null_value_decimal_rate": 0.12,
    "distinct_categories": 1.0,
    "avg_value_decimal": 2.5,
}


def _load_features() -> dict[str, Any]:
    payload = os.getenv("DECISION_FEATURES_JSON")
    if payload is None:
        return dict(DEFAULT_FEATURES)

    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("DECISION_FEATURES_JSON must decode to a JSON object")

    return {str(key): value for key, value in parsed.items()}


def main() -> int:
    logger = get_logger(__name__)
    db = SessionLocal()
    tracker = RunTracker(db, logger, pipeline="decisions", input_ref="policy_v0")

    features: dict[str, Any] = {}

    try:
        with tracker.step("build_features"):
            features = _load_features()
            tracker.log("features_built", feature_count=len(features))

        with tracker.step("evaluate_policy_v0"):
            result = evaluate(features)
            tracker.log(
                "policy_evaluated",
                decision=result.decision,
                score=result.score,
                policy_version=result.policy_version,
                policy_hash=result.policy_hash,
            )

        with tracker.step("write_decision"):
            persisted = write_decision(db, tracker.run_id, result)
            tracker.log(
                "decision_written",
                decision=persisted.decision,
                score=persisted.score,
                reason_count=len(persisted.reasons or []),
            )

        with tracker.step("write_decision_output"):
            persisted_output = save_decision_output(
                db,
                result,
                features,
                meta={
                    "pipeline_run_id": str(tracker.run_id),
                    "policy_hash": result.policy_hash,
                },
            )
            tracker.log(
                "decision_output_written",
                decision_output_id=str(persisted_output.id),
                input_hash=persisted_output.input_hash,
            )

        tracker.succeed(records_in=len(features), records_out=1)

        print(
            json.dumps(
                {
                    "pipeline": "decisions",
                    "run_id": str(tracker.run_id),
                    "decision": persisted.decision,
                    "score": persisted.score,
                    "policy_version": persisted.policy_version,
                    "policy_hash": persisted.policy_hash,
                    "reasons": persisted.reasons,
                },
                sort_keys=True,
            )
        )
        return 0

    except Exception as exc:
        tracker.fail(exc, records_in=len(features) or None, records_out=0)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
