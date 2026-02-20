from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

DecisionLabel = Literal["approve", "review", "reject"]


@dataclass(frozen=True, slots=True)
class PolicyRule:
    code: str
    feature: str
    operator: str
    value: float
    penalty: int
    reason: str


@dataclass(frozen=True, slots=True)
class DecisionInput:
    total_clean_records: Any = None
    null_value_decimal_rate: Any = None
    distinct_categories: Any = None
    avg_value_decimal: Any = None
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> DecisionInput:
        known_keys = {
            "total_clean_records",
            "null_value_decimal_rate",
            "distinct_categories",
            "avg_value_decimal",
        }
        return cls(
            total_clean_records=payload.get("total_clean_records"),
            null_value_decimal_rate=payload.get("null_value_decimal_rate"),
            distinct_categories=payload.get("distinct_categories"),
            avg_value_decimal=payload.get("avg_value_decimal"),
            extras={
                str(key): value
                for key, value in payload.items()
                if str(key) not in known_keys
            },
        )

    def to_feature_map(self) -> dict[str, Any]:
        features = {
            "total_clean_records": self.total_clean_records,
            "null_value_decimal_rate": self.null_value_decimal_rate,
            "distinct_categories": self.distinct_categories,
            "avg_value_decimal": self.avg_value_decimal,
        }
        features.update(self.extras)
        return features


@dataclass(frozen=True, slots=True)
class DecisionResult:
    policy_version: str
    policy_hash: str
    decision: DecisionLabel
    score: int
    reasons: list[str]
    explanation_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    policy_version: str
    score_start: int = 100
    approve_min: int = 80
    review_min: int = 50
    rules: tuple[PolicyRule, ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_version:
            raise ValueError("policy_version is required")
        if self.approve_min < self.review_min:
            raise ValueError("approve_min must be greater than or equal to review_min")

    def snapshot(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "score_start": self.score_start,
            "thresholds": {
                "approve_min": self.approve_min,
                "review_min": self.review_min,
            },
            "rules": [
                {
                    "code": rule.code,
                    "feature": rule.feature,
                    "operator": rule.operator,
                    "value": rule.value,
                    "penalty": rule.penalty,
                    "reason": rule.reason,
                }
                for rule in self.rules
            ],
        }

    def evaluate(self, input_payload: DecisionInput | Mapping[str, Any]) -> DecisionResult:
        resolved_input = (
            input_payload
            if isinstance(input_payload, DecisionInput)
            else DecisionInput.from_mapping(input_payload)
        )
        features = resolved_input.to_feature_map()

        hits: list[dict[str, Any]] = []
        used_features: dict[str, float | None] = {}

        for rule in self.rules:
            actual_raw = _as_number(features.get(rule.feature))
            actual = _round_number(actual_raw) if actual_raw is not None else None
            used_features[rule.feature] = actual

            if actual is None:
                continue

            threshold = _round_number(float(rule.value))
            if not _matches(rule.operator, actual, threshold):
                continue

            hits.append(
                {
                    "code": rule.code,
                    "delta": -int(rule.penalty),
                    "reason": rule.reason,
                    "details": {
                        "feature": rule.feature,
                        "operator": rule.operator,
                        "threshold": threshold,
                        "actual": actual,
                    },
                }
            )

        hits.sort(key=lambda hit: (-abs(int(hit["delta"])), str(hit["code"])))

        score = max(0, int(self.score_start) + sum(int(hit["delta"]) for hit in hits))
        decision = _decision_for_score(
            score,
            approve_min=self.approve_min,
            review_min=self.review_min,
        )

        policy_hash = compute_policy_hash(self.snapshot())
        reasons = [str(hit["reason"]) for hit in hits]
        feature_snapshot = {name: used_features[name] for name in sorted(used_features)}

        explanation_json = {
            "policy_version": self.policy_version,
            "policy_hash": policy_hash,
            "thresholds": {
                "approve_min": self.approve_min,
                "review_min": self.review_min,
            },
            "threshold_semantics": (
                "approve if score >= approve_min; "
                "review if score >= review_min; "
                "reject otherwise"
            ),
            "score_start": self.score_start,
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
            policy_version=self.policy_version,
            policy_hash=policy_hash,
            decision=decision,
            score=score,
            reasons=reasons,
            explanation_json=explanation_json,
        )


def compute_policy_hash(snapshot: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(snapshot), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _round_number(value: float, *, places: int = 6) -> float:
    return round(float(value), places)


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


def _decision_for_score(score: int, *, approve_min: int, review_min: int) -> DecisionLabel:
    # Threshold semantics are inclusive: score >= threshold qualifies.
    if score >= approve_min:
        return "approve"
    if score >= review_min:
        return "review"
    return "reject"


POLICY_VERSION = "v0"
POLICY_RULES = (
    PolicyRule(
        code="LOW_RECORD_VOLUME",
        feature="total_clean_records",
        operator="<",
        value=5,
        penalty=21,
        reason="record volume below minimum baseline",
    ),
    PolicyRule(
        code="HIGH_NULL_RATE",
        feature="null_value_decimal_rate",
        operator=">",
        value=0.10,
        penalty=20,
        reason="null numeric value rate is elevated",
    ),
    PolicyRule(
        code="LOW_CATEGORY_DIVERSITY",
        feature="distinct_categories",
        operator="<",
        value=2,
        penalty=12,
        reason="category diversity is too low",
    ),
    PolicyRule(
        code="LOW_AVG_VALUE",
        feature="avg_value_decimal",
        operator="<",
        value=3,
        penalty=8,
        reason="average numeric value is too low",
    ),
)
DEFAULT_POLICY = DecisionPolicy(policy_version=POLICY_VERSION, rules=POLICY_RULES)
POLICY_SNAPSHOT = DEFAULT_POLICY.snapshot()


def evaluate(features: Mapping[str, Any]) -> DecisionResult:
    return DEFAULT_POLICY.evaluate(features)
