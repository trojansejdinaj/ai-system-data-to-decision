from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FeatureDtype = Literal["num", "text", "json"]


@dataclass(frozen=True)
class FeatureDef:
    name: str
    dtype: FeatureDtype
    meaning: str
    formula: str


_FEATURE_DEFS: tuple[FeatureDef, ...] = (
    FeatureDef(
        name="total_clean_records",
        dtype="num",
        meaning="Total count of clean records in the dataset scope.",
        formula="Count all clean records whose source equals the dataset key.",
    ),
    FeatureDef(
        name="distinct_sources",
        dtype="num",
        meaning="Distinct number of source labels in scope.",
        formula="Count distinct source values among clean records in dataset scope.",
    ),
    FeatureDef(
        name="distinct_categories",
        dtype="num",
        meaning="Distinct non-null categories in scope.",
        formula="Count distinct non-null category values in dataset scope.",
    ),
    FeatureDef(
        name="sum_value_decimal",
        dtype="num",
        meaning="Sum of value_decimal across non-null rows in scope.",
        formula="Sum value_decimal over rows in dataset scope where value_decimal is present.",
    ),
    FeatureDef(
        name="avg_value_decimal",
        dtype="num",
        meaning="Average of value_decimal across non-null rows in scope.",
        formula="Average value_decimal over rows in dataset scope where value_decimal is present.",
    ),
    FeatureDef(
        name="null_value_decimal_rate",
        dtype="num",
        meaning="Share of rows where value_decimal is null.",
        formula="Divide rows with null value_decimal by total rows in dataset scope.",
    ),
)


def get_feature_defs() -> list[FeatureDef]:
    return list(_FEATURE_DEFS)
