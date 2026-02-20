from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .policy import POLICY_VERSION, decision_for_score, extract_features, score_features


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision: str
    score: int
    reasons: list[str]
    top_reason: str
    policy_version: str


def make_decision_summary(
    flagged_records: list[Any],
    meta: Mapping[str, Any] | None = None,
) -> DecisionResult:
    features = extract_features(flagged_records, meta=meta)
    score, reasons = score_features(features)
    decision = decision_for_score(score)
    top_reason = reasons[0] if reasons else "no_flags_detected"
    return DecisionResult(
        decision=decision,
        score=score,
        reasons=reasons,
        top_reason=top_reason,
        policy_version=POLICY_VERSION,
    )
