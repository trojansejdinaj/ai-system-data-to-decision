from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

POLICY_VERSION = "v0"
POLICY_SNAPSHOT: dict[str, Any] = {
    "policy_version": POLICY_VERSION,
    "score_start": 100,
    "thresholds": {
        "approve_min": 80,
        "review_min": 50,
    },
    "rules": [
        {
            "code": "LOW_RECORD_VOLUME",
            "feature": "total_clean_records",
            "operator": "<",
            "value": 5,
            "penalty": 21,
            "reason": "record volume below minimum baseline",
        },
        {
            "code": "HIGH_NULL_RATE",
            "feature": "null_value_decimal_rate",
            "operator": ">",
            "value": 0.10,
            "penalty": 20,
            "reason": "null numeric value rate is elevated",
        },
        {
            "code": "LOW_CATEGORY_DIVERSITY",
            "feature": "distinct_categories",
            "operator": "<",
            "value": 2,
            "penalty": 12,
            "reason": "category diversity is too low",
        },
        {
            "code": "LOW_AVG_VALUE",
            "feature": "avg_value_decimal",
            "operator": "<",
            "value": 3,
            "penalty": 8,
            "reason": "average numeric value is too low",
        },
    ],
}


@dataclass(frozen=True, slots=True)
class DecisionResult:
    policy_version: str
    policy_hash: str
    decision: str
    score: int
    reasons: list[str]
    explanation_json: dict[str, Any]


def compute_policy_hash(snapshot: dict[str, Any]) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _as_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _matches(operator: str, actual: float, threshold: float) -> bool:
    if operator == "<":
        return actual < threshold
    if operator == "<=":
        return actual <= threshold
    if operator == ">":
        return actual > threshold
    if operator == ">=":
        return actual >= threshold
    if operator == "==":
        return actual == threshold
    if operator == "!=":
        return actual != threshold
    raise ValueError(f"Unsupported operator: {operator}")


def evaluate(features: dict[str, Any]) -> DecisionResult:
    score_start = int(POLICY_SNAPSHOT["score_start"])
    thresholds = dict(POLICY_SNAPSHOT["thresholds"])

    hits: list[dict[str, Any]] = []
    used_features: dict[str, float | None] = {}

    for rule in POLICY_SNAPSHOT["rules"]:
        feature_name = str(rule["feature"])
        actual = _as_number(features.get(feature_name))
        used_features[feature_name] = actual

        if actual is None:
            continue

        threshold = float(rule["value"])
        operator = str(rule["operator"])
        if not _matches(operator, actual, threshold):
            continue

        penalty = int(rule["penalty"])
        hits.append(
            {
                "code": str(rule["code"]),
                "delta": -penalty,
                "reason": str(rule["reason"]),
                "details": {
                    "feature": feature_name,
                    "operator": operator,
                    "threshold": threshold,
                    "actual": actual,
                },
            }
        )

    hits.sort(key=lambda hit: (-abs(int(hit["delta"])), str(hit["code"])))

    score = max(0, score_start + sum(int(hit["delta"]) for hit in hits))
    approve_min = int(thresholds["approve_min"])
    review_min = int(thresholds["review_min"])

    if score >= approve_min:
        decision = "approve"
    elif score >= review_min:
        decision = "review"
    else:
        decision = "reject"

    policy_hash = compute_policy_hash(POLICY_SNAPSHOT)
    reasons = [str(hit["reason"]) for hit in hits]
    feature_snapshot = {name: used_features[name] for name in sorted(used_features)}

    explanation_json = {
        "policy_version": POLICY_VERSION,
        "policy_hash": policy_hash,
        "thresholds": thresholds,
        "score_start": score_start,
        "score_end": score,
        "feature_snapshot": feature_snapshot,
        "rule_hits": [
            {
                "code": hit["code"],
                "delta": hit["delta"],
                "details": hit["details"],
            }
            for hit in hits
        ],
    }

    return DecisionResult(
        policy_version=POLICY_VERSION,
        policy_hash=policy_hash,
        decision=decision,
        score=score,
        reasons=reasons,
        explanation_json=explanation_json,
    )
