from __future__ import annotations

import hashlib
import json

from app.decision_policy.policy_v0 import (
    POLICY_SNAPSHOT,
    DecisionPolicy,
    PolicyRule,
    compute_policy_hash,
    evaluate,
)


def test_evaluate_is_deterministic_for_same_input() -> None:
    features = {
        "total_clean_records": 4,
        "null_value_decimal_rate": 0.12,
        "distinct_categories": 1,
        "avg_value_decimal": 2.5,
    }

    first = evaluate(features)
    second = evaluate(dict(features))

    assert first.decision == second.decision
    assert first.score == second.score
    assert first.reasons == second.reasons
    assert first.policy_hash == second.policy_hash
    assert first.explanation_json == second.explanation_json


def test_policy_hash_uses_canonical_serialization() -> None:
    canonical = json.dumps(POLICY_SNAPSHOT, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    assert compute_policy_hash(POLICY_SNAPSHOT) == expected
    assert len(expected) == 64


def test_reasons_and_rule_hits_are_ordered_by_penalty_desc() -> None:
    features = {
        "total_clean_records": 4,
        "null_value_decimal_rate": 0.12,
        "distinct_categories": 1,
        "avg_value_decimal": 2.5,
    }

    result = evaluate(features)
    hits = result.explanation_json["rule_hits"]

    assert [h["code"] for h in hits] == [
        "LOW_RECORD_VOLUME",
        "HIGH_NULL_RATE",
        "LOW_CATEGORY_DIVERSITY",
        "LOW_AVG_VALUE",
    ]
    assert [abs(int(h["delta"])) for h in hits] == [21, 20, 12, 8]
    assert result.top_reason == "record volume below minimum baseline"


def test_reason_ordering_uses_penalty_then_rule_code_tie_break() -> None:
    policy = DecisionPolicy(
        policy_version="v0-test",
        rules=(
            PolicyRule(
                code="RULE_B",
                feature="f_b",
                operator=">",
                value=0,
                penalty=10,
                reason="reason-b",
            ),
            PolicyRule(
                code="RULE_A",
                feature="f_a",
                operator=">",
                value=0,
                penalty=10,
                reason="reason-a",
            ),
        ),
    )

    result = policy.evaluate({"f_a": 1, "f_b": 1})

    assert result.reasons == ["reason-a", "reason-b"]
    assert result.top_reason == "reason-a"
    assert [hit["code"] for hit in result.explanation_json["rule_hits"]] == ["RULE_A", "RULE_B"]


def test_threshold_boundaries_80_and_79() -> None:
    score_80 = evaluate(
        {
            "total_clean_records": 10,
            "null_value_decimal_rate": 0.11,
            "distinct_categories": 3,
            "avg_value_decimal": 10,
        }
    )
    assert score_80.score == 80
    assert score_80.decision == "approve"

    score_79 = evaluate(
        {
            "total_clean_records": 4,
            "null_value_decimal_rate": 0.0,
            "distinct_categories": 3,
            "avg_value_decimal": 10,
        }
    )
    assert score_79.score == 79
    assert score_79.decision == "review"
