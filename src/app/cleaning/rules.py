from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


NULL_LITERALS = {
    "",
    " ",
    "na",
    "n/a",
    "none",
    "null",
    "nil",
    "-",
    "--",
    "—",
}


def is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip().lower()
        return v in NULL_LITERALS
    return False


def to_null(value: Any) -> None:
    return None


def normalize_text(value: Any) -> str | None:
    if is_null(value):
        return None
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)
    return s or None


def normalize_category(value: Any, mapping: dict[str, str]) -> str | None:
    """
    Maps raw categories to canonical values.
    Matching is case-insensitive after trim.
    """
    raw = normalize_text(value)
    if raw is None:
        return None
    key = raw.lower()
    return mapping.get(key, raw)  # if unknown, keep the cleaned original


_DATE_FORMATS = (
    "%Y-%m-%d",          # 2026-01-09
    "%Y/%m/%d",          # 2026/01/09
    "%d/%m/%Y",          # 09/01/2026
    "%m/%d/%Y",          # 01/09/2026 (ambiguous)
    "%d-%m-%Y",          # 09-01-2026
    "%m-%d-%Y",          # 01-09-2026
    "%Y-%m-%dT%H:%M:%S", # 2026-01-09T12:30:00
    "%Y-%m-%d %H:%M:%S", # 2026-01-09 12:30:00
)


def normalize_date(value: Any, *, day_first: bool = True) -> date | None:
    """
    Rule:
    - Accepts common formats (ISO, slash, datetime strings)
    - If ambiguous (01/09/2026), uses `day_first` preference.
    - Returns Python `date`.
    """
    if is_null(value):
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    s = str(value).strip()

    # Fast path: ISO date
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        pass

    # Handle ambiguous slash formats explicitly
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", s):
        d1, d2, y = s.split("/")
        a, b = int(d1), int(d2)
        if day_first:
            # dd/mm/yyyy
            try:
                return date(int(y), b, a)
            except Exception:
                return None
        else:
            # mm/dd/yyyy
            try:
                return date(int(y), a, b)
            except Exception:
                return None

    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date()
        except Exception:
            continue

    return None


_CURRENCY_CLEAN_RE = re.compile(r"[^\d,.\-]")


def normalize_currency_to_decimal(value: Any) -> Decimal | None:
    """
    Rule:
    - Removes currency symbols and spaces
    - Supports '1,234.56' and '1.234,56' (EU style)
    - Returns Decimal (exact), or None if invalid/null
    """
    if is_null(value):
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        # Convert through string to avoid float binary noise in most common cases
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    s = str(value).strip()
    s = _CURRENCY_CLEAN_RE.sub("", s)

    if not s:
        return None

    # Detect EU style: "1.234,56" -> "1234.56"
    if s.count(",") == 1 and s.count(".") >= 1 and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        # Common style: "1,234.56" -> remove commas
        if s.count(".") <= 1:
            s = s.replace(",", "")

    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def normalize_int(value: Any) -> int | None:
    if is_null(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    s = normalize_text(value)
    if s is None:
        return None
    s = s.replace(",", "")
    try:
        return int(float(s))
    except Exception:
        return None


def normalize_float(value: Any) -> float | None:
    if is_null(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = normalize_text(value)
    if s is None:
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return None


@dataclass(frozen=True)
class OutlierRule:
    """
    Simple guardrail outlier rule:
    - If numeric value is outside [min_value, max_value], set to None.
    """
    min_value: float | None = None
    max_value: float | None = None

    def apply(self, value: float | int | None) -> float | int | None:
        if value is None:
            return None
        v = float(value)
        if self.min_value is not None and v < self.min_value:
            return None
        if self.max_value is not None and v > self.max_value:
            return None
        return value


def strip_unknown_keys(row: dict[str, Any], allowed: set[str] | None) -> dict[str, Any]:
    if not allowed:
        return dict(row)
    return {k: v for k, v in row.items() if k in allowed}


def normalize_nulls(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        out[k] = None if is_null(v) else v
    return out


def sample_before_after(before: dict[str, Any], after: dict[str, Any], *, keys: Iterable[str]) -> str:
    lines = ["| field | before | after |", "|---|---|---|"]
    for k in keys:
        lines.append(f"| {k} | {before.get(k)!r} | {after.get(k)!r} |")
    return "\n".join(lines)
