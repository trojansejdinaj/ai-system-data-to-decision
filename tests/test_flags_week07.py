# Tests (no DB needed)
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.flags.engine import flag_records


def test_week07_flags_rules_and_severity_are_deterministic():
    now = datetime(2026, 1, 16, tzinfo=UTC)

    records = [
        # Empty value -> VALUE_EMPTY_OR_NULLISH (40)
        {
            "id": "1",
            "source": "s",
            "source_id": "A",
            "category": "c",
            "event_time": now.isoformat(),
            "value": "   ",
        },
        # Non-numeric -> VALUE_NOT_NUMERIC (40)
        {
            "id": "2",
            "source": "s",
            "source_id": "B",
            "category": "c",
            "event_time": now.isoformat(),
            "value": "abc",
        },
        # Future event_time (25) + out_of_range (35) => 60
        {
            "id": "3",
            "source": "s",
            "source_id": "C",
            "category": "c",
            "event_time": (now + timedelta(days=1)).isoformat(),
            "value": "-5",
        },
        # Duplicate fingerprint (30) each
        {
            "id": "4",
            "source": "s",
            "source_id": "D",
            "category": "c",
            "event_time": now.isoformat(),
            "value": "10",
        },
        {
            "id": "5",
            "source": "s",
            "source_id": "D",
            "category": "c",
            "event_time": now.isoformat(),
            "value": "10",
        },
    ]

    flagged = flag_records(records, now=now)
    assert len(flagged) == 5

    r1 = next(fr for fr in flagged if fr.record["id"] == "1")
    assert r1.severity == 40
    assert "VALUE_EMPTY_OR_NULLISH" in r1.flag_codes

    r2 = next(fr for fr in flagged if fr.record["id"] == "2")
    assert r2.severity == 40
    assert "VALUE_NOT_NUMERIC" in r2.flag_codes

    r3 = next(fr for fr in flagged if fr.record["id"] == "3")
    assert r3.severity == 60
    assert "FUTURE_EVENT_TIME" in r3.flag_codes
    assert "VALUE_OUT_OF_RANGE" in r3.flag_codes

    r4 = next(fr for fr in flagged if fr.record["id"] == "4")
    r5 = next(fr for fr in flagged if fr.record["id"] == "5")
    assert "POSSIBLE_DUPLICATE_FINGERPRINT" in r4.flag_codes
    assert "POSSIBLE_DUPLICATE_FINGERPRINT" in r5.flag_codes
