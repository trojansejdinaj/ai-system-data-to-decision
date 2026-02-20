from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

POLICY_VERSION = "v1"
_BASE_SCORE = 100

_REASON_PRIORITY = {
    "high_severity_flags": 0,
    "high_flag_density": 1,
    "duplicate_fingerprint_flags": 2,
    "low_risk_flags_only": 3,
    "no_flags_detected": 4,
}


@dataclass(frozen=True, slots=True)
class DecisionFeatures:
    total_records: int
    flagged_count: int
    flagged_ratio: float
    max_severity: int
    has_duplicate_fingerprint_flags: bool


def extract_features(
    flagged_records: Iterable[Any],
    meta: Mapping[str, Any] | None = None,
) -> DecisionFeatures:
    rows = list(flagged_records)
    resolved_total = _to_int((meta or {}).get("total_records"))
    total_records = max(len(rows), resolved_total or 0)
    flagged_count = len(rows)
    flagged_ratio = (flagged_count / total_records) if total_records > 0 else 0.0

    severities = [_extract_severity(row) for row in rows]
    max_severity = max(severities) if severities else 0

    has_duplicate = False
    for row in rows:
        codes = _extract_flag_codes(row)
        if any("DUPLICATE" in code.upper() for code in codes):
            has_duplicate = True
            break

    return DecisionFeatures(
        total_records=total_records,
        flagged_count=flagged_count,
        flagged_ratio=flagged_ratio,
        max_severity=max_severity,
        has_duplicate_fingerprint_flags=has_duplicate,
    )


def score_features(features: DecisionFeatures) -> tuple[int, list[str]]:
    score = _BASE_SCORE
    reasons: list[str] = []

    if features.flagged_count == 0:
        reasons.append("no_flags_detected")
    else:
        if features.max_severity >= 60:
            score -= 40
            reasons.append("high_severity_flags")
        if features.flagged_ratio >= 0.30:
            score -= 20
            reasons.append("high_flag_density")
        if features.has_duplicate_fingerprint_flags:
            score -= 10
            reasons.append("duplicate_fingerprint_flags")
        if not reasons:
            reasons.append("low_risk_flags_only")

    score = clamp_score(score)
    reasons = ordered_reasons(reasons)
    return score, reasons


def decision_for_score(score: int) -> str:
    score = clamp_score(score)
    if score >= 80:
        return "approve"
    if score >= 50:
        return "review"
    return "reject"


def clamp_score(score: int) -> int:
    return max(0, min(100, int(score)))


def ordered_reasons(reasons: Iterable[str]) -> list[str]:
    unique = {str(reason) for reason in reasons}
    return sorted(unique, key=lambda reason: (_REASON_PRIORITY.get(reason, 999), reason))


def _extract_severity(flagged_record: Any) -> int:
    if hasattr(flagged_record, "severity"):
        return _to_int(flagged_record.severity) or 0
    if isinstance(flagged_record, Mapping):
        return _to_int(flagged_record.get("severity")) or 0
    return 0


def _extract_flag_codes(flagged_record: Any) -> list[str]:
    raw_flags: list[Any] = []
    if hasattr(flagged_record, "flags"):
        raw_flags = list(flagged_record.flags or [])
    elif isinstance(flagged_record, Mapping):
        raw_flags = list(flagged_record.get("flags") or [])

    codes: list[str] = []
    for raw_flag in raw_flags:
        if hasattr(raw_flag, "code"):
            code = str(raw_flag.code)
        elif isinstance(raw_flag, Mapping):
            code = str(raw_flag.get("code", ""))
        else:
            code = ""
        if code:
            codes.append(code)
    return codes


def _to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
