from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from .models import Flag

RuleFn = Callable[[dict[str, Any], datetime], Flag | None]

# deterministic "null-ish" set for text fields
NULLISH = {"null", "none", "na", "n/a", "nil", "-"}


def _get_dt(record: dict[str, Any], key: str) -> datetime | None:
    v = record.get(key)
    if v is None:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=UTC)
    if isinstance(v, str):
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _value_str(record: dict[str, Any]) -> str:
    v = record.get("value")
    return "" if v is None else str(v)


def _parse_value_float(record: dict[str, Any]) -> float | None:
    s = _value_str(record).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def rule_value_empty_or_nullish(record: dict[str, Any], now: datetime) -> Flag | None:
    s = _value_str(record).strip()
    if (not s) or (s.lower() in NULLISH):
        return Flag(
            code="VALUE_EMPTY_OR_NULLISH",
            weight=40,
            message=f"value='{s}' is empty or null-ish",
        )
    return None


def rule_value_not_numeric(record: dict[str, Any], now: datetime) -> Flag | None:
    s = _value_str(record).strip()
    if (not s) or (s.lower() in NULLISH):
        return None  # handled by VALUE_EMPTY_OR_NULLISH
    x = _parse_value_float(record)
    if x is None:
        return Flag(
            code="VALUE_NOT_NUMERIC",
            weight=40,
            message=f"value='{s}' cannot be parsed as float",
        )
    return None


def rule_future_event_time(record: dict[str, Any], now: datetime) -> Flag | None:
    event_time = _get_dt(record, "event_time")
    if event_time is None:
        return Flag(code="EVENT_TIME_INVALID", weight=40, message="event_time could not be parsed")
    if event_time > (now + timedelta(minutes=5)):
        return Flag(
            code="FUTURE_EVENT_TIME",
            weight=25,
            message=(
                f"event_time={event_time.isoformat()} is in the future "
                f"vs now={now.isoformat()}"
            ),
        )
    return None


def rule_stale_event_time(record: dict[str, Any], now: datetime) -> Flag | None:
    event_time = _get_dt(record, "event_time")
    if event_time is None:
        return None
    if event_time < (now - timedelta(days=30)):
        return Flag(
            code="STALE_EVENT_TIME",
            weight=15,
            message=f"event_time={event_time.date().isoformat()} is older than 30 days",
        )
    return None


def rule_value_out_of_range(record: dict[str, Any], now: datetime) -> Flag | None:
    x = _parse_value_float(record)
    if x is None:
        return None  # empty/non-numeric handled elsewhere
    if x <= 0:
        return Flag(code="VALUE_OUT_OF_RANGE", weight=35, message=f"value={x} must be > 0")
    if x > 1_000_000:
        return Flag(code="VALUE_OUT_OF_RANGE", weight=35, message=f"value={x} exceeds 1,000,000")
    return None


def build_rules() -> list[RuleFn]:
    # deterministic order matters for stable outputs
    return [
        rule_value_empty_or_nullish,
        rule_value_not_numeric,
        rule_future_event_time,
        rule_stale_event_time,
        rule_value_out_of_range,
    ]


def fingerprint(record: dict[str, Any]) -> tuple[Any, ...]:
    # batch duplicate fingerprint, deterministic
    return (
        record.get("source"),
        record.get("source_id"),
        record.get("event_time"),
        record.get("category"),
        record.get("value"),
    )
