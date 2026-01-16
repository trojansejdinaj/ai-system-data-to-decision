from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .rules import (
    OutlierRule,
    normalize_category,
    normalize_currency_to_decimal,
    normalize_date,
    normalize_float,
    normalize_int,
    normalize_nulls,
    normalize_text,
    strip_unknown_keys,
)


@dataclass(frozen=True)
class CleaningConfig:
    """
    Week 03 config: explicit, boring, predictable.
    """

    # If set, remove keys not in this set
    allowed_keys: set[str] | None = None

    # Date parsing preference for ambiguous formats like 01/09/2026
    day_first: bool = True

    # Canonical category mapping: key should be lowercase/trimmed
    category_mapping: dict[str, str] = None  # type: ignore[assignment]

    # Per-field outlier rules (after numeric parsing)
    outlier_rules: dict[str, OutlierRule] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "category_mapping", self.category_mapping or {})
        object.__setattr__(self, "outlier_rules", self.outlier_rules or {})


def clean_row(row: dict[str, Any], cfg: CleaningConfig) -> dict[str, Any]:
    row = strip_unknown_keys(row, cfg.allowed_keys)
    row = normalize_nulls(row)

    out: dict[str, Any] = dict(row)

    # Common normalizations by conventional field names
    # (You can expand this as your schema stabilizes.)
    if "title" in out:
        out["title"] = normalize_text(out["title"])

    if "category" in out:
        out["category"] = normalize_category(out["category"], cfg.category_mapping)

    if "published_at" in out:
        out["published_at"] = normalize_date(out["published_at"], day_first=cfg.day_first)

    if "created_at" in out:
        out["created_at"] = normalize_date(out["created_at"], day_first=cfg.day_first)

    if "price" in out:
        out["price"] = normalize_currency_to_decimal(out["price"])

    if "revenue" in out:
        out["revenue"] = normalize_currency_to_decimal(out["revenue"])

    if "views" in out:
        out["views"] = normalize_int(out["views"])

    if "score" in out:
        out["score"] = normalize_float(out["score"])

    # Apply outlier rules
    for field, rule in cfg.outlier_rules.items():
        if field not in out:
            continue
        val = out[field]
        if isinstance(val, Decimal):
            # outlier rules are numeric float bounds; convert safely
            try:
                out[field] = rule.apply(float(val))
            except Exception:
                out[field] = None
        elif isinstance(val, (int, float)) or val is None:
            out[field] = rule.apply(val)
        else:
            # If it's not numeric after parsing, treat as invalid for numeric outlier rules
            out[field] = None

    return out


def clean_rows(rows: list[dict[str, Any]], cfg: CleaningConfig) -> list[dict[str, Any]]:
    return [clean_row(r, cfg) for r in rows]
