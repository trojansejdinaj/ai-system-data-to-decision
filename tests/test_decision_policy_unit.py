from __future__ import annotations

import pytest

from app.decision import compute_input_hash
from app.decision_policy.policy_v0 import DecisionPolicy, PolicyRule


def _build_threshold_test_policy(*, policy_version: str = "v1") -> DecisionPolicy:
    return DecisionPolicy(
        policy_version=policy_version,
        approve_min=80,
        review_min=50,
        rules=(
            PolicyRule(
                code="PENALTY_19",
                feature="f19",
                operator="<",
                value=1,
                penalty=19,
                reason="penalty 19",
            ),
            PolicyRule(
                code="PENALTY_20",
                feature="f20",
                operator="<",
                value=1,
                penalty=20,
                reason="penalty 20",
            ),
            PolicyRule(
                code="PENALTY_21",
                feature="f21",
                operator="<",
                value=1,
                penalty=21,
                reason="penalty 21",
            ),
            PolicyRule(
                code="PENALTY_49",
                feature="f49",
                operator="<",
                value=1,
                penalty=49,
                reason="penalty 49",
            ),
            PolicyRule(
                code="PENALTY_50",
                feature="f50",
                operator="<",
                value=1,
                penalty=50,
                reason="penalty 50",
            ),
            PolicyRule(
                code="PENALTY_51",
                feature="f51",
                operator="<",
                value=1,
                penalty=51,
                reason="penalty 51",
            ),
        ),
    )


def _input_with_penalties(*, trigger: set[str]) -> dict[str, int]:
    payload = {"f19": 1, "f20": 1, "f21": 1, "f49": 1, "f50": 1, "f51": 1}
    for feature in trigger:
        payload[feature] = 0
    return payload


@pytest.mark.parametrize(
    ("trigger", "expected_score", "expected_decision", "expected_reasons"),
    [
        ({"f19"}, 81, "approve", ["penalty 19"]),
        ({"f20"}, 80, "approve", ["penalty 20"]),
        ({"f21"}, 79, "review", ["penalty 21"]),
        ({"f49"}, 51, "review", ["penalty 49"]),
        ({"f50"}, 50, "review", ["penalty 50"]),
        ({"f51"}, 49, "reject", ["penalty 51"]),
    ],
)
def test_threshold_boundaries_are_intentional_and_inclusive(
    trigger: set[str],
    expected_score: int,
    expected_decision: str,
    expected_reasons: list[str],
) -> None:
    policy = _build_threshold_test_policy()
    result = policy.evaluate(_input_with_penalties(trigger=trigger))

    assert result.score == expected_score
    assert result.decision == expected_decision
    assert result.reasons == expected_reasons


def test_determinism_same_input_and_policy_version() -> None:
    policy = _build_threshold_test_policy(policy_version="v1")
    payload = _input_with_penalties(trigger={"f21", "f50", "f19"})

    first = policy.evaluate(payload)
    second = policy.evaluate(dict(payload))

    assert first == second

    expected_reason_order = ["penalty 50", "penalty 21", "penalty 19"]
    assert first.reasons == expected_reason_order

    payload_reordered = {
        "f50": payload["f50"],
        "f19": payload["f19"],
        "f21": payload["f21"],
        "f49": payload["f49"],
        "f20": payload["f20"],
        "f51": payload["f51"],
    }
    assert compute_input_hash(payload) == compute_input_hash(payload_reordered)
