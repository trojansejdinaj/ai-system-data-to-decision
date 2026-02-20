from __future__ import annotations

from app.decision_policy.service import make_decision_summary
from app.flags.models import Flag, FlaggedRecord


def test_policy_is_deterministic_for_controlled_flags() -> None:
    flagged_records = [
        FlaggedRecord(
            record={"id": "a"},
            severity=70,
            flags=[Flag(code="VALUE_EMPTY_OR_NULLISH", weight=40, message="value is empty")],
        ),
        FlaggedRecord(
            record={"id": "b"},
            severity=35,
            flags=[
                Flag(
                    code="POSSIBLE_DUPLICATE_FINGERPRINT", weight=30, message="duplicate batch fp"
                ),
            ],
        ),
    ]

    first = make_decision_summary(flagged_records, meta={"total_records": 5})
    second = make_decision_summary(list(flagged_records), meta={"total_records": 5})

    assert first == second
    assert first.score == 30
    assert first.decision == "reject"
    assert first.reasons == [
        "high_severity_flags",
        "high_flag_density",
        "duplicate_fingerprint_flags",
    ]
    assert first.top_reason == "high_severity_flags"


def test_policy_no_flags_detected_path() -> None:
    result = make_decision_summary([], meta={"total_records": 10})

    assert result.score == 100
    assert result.decision == "approve"
    assert result.reasons == ["no_flags_detected"]
    assert result.top_reason == "no_flags_detected"


def test_reason_priority_is_explicit_and_top_reason_is_stable() -> None:
    flagged_records = [
        FlaggedRecord(
            record={"id": "x"},
            severity=70,
            flags=[
                Flag(code="POSSIBLE_DUPLICATE_FINGERPRINT", weight=30, message="duplicate fp"),
            ],
        ),
        FlaggedRecord(
            record={"id": "y"},
            severity=15,
            flags=[Flag(code="VALUE_EMPTY_OR_NULLISH", weight=10, message="empty value")],
        ),
    ]

    result = make_decision_summary(flagged_records, meta={"total_records": 4})

    assert result.reasons == [
        "high_severity_flags",
        "high_flag_density",
        "duplicate_fingerprint_flags",
    ]
    assert result.top_reason == "high_severity_flags"
