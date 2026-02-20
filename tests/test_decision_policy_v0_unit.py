from __future__ import annotations

import hashlib
import json

from app.decisions.policy_v0 import POLICY_SNAPSHOT, compute_policy_hash, evaluate


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
