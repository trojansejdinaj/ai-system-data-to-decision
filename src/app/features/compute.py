from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models import FeatureValue
from app.features.feature_definitions import FeatureDef, get_feature_defs


def _to_decimal_or_zero(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def compute_numeric_features(aggregates: Mapping[str, Any]) -> dict[str, Decimal]:
    total_clean_records = int(aggregates.get("total_clean_records") or 0)
    null_value_decimal_count = int(aggregates.get("null_value_decimal_count") or 0)
    null_value_decimal_rate = Decimal("0")
    if total_clean_records > 0:
        null_value_decimal_rate = (
            Decimal(null_value_decimal_count) / Decimal(total_clean_records)
        ).quantize(Decimal("0.000001"))

    return {
        "total_clean_records": Decimal(total_clean_records),
        "distinct_sources": Decimal(int(aggregates.get("distinct_sources") or 0)),
        "distinct_categories": Decimal(int(aggregates.get("distinct_categories") or 0)),
        "sum_value_decimal": _to_decimal_or_zero(aggregates.get("sum_value_decimal")),
        "avg_value_decimal": _to_decimal_or_zero(aggregates.get("avg_value_decimal")),
        "null_value_decimal_rate": null_value_decimal_rate,
    }


def _fetch_clean_aggregates(session: Session, dataset_key: str) -> Mapping[str, Any]:
    result = (
        session.execute(
            text(
                """
                SELECT
                  COUNT(*)::bigint AS total_clean_records,
                  COUNT(DISTINCT source)::bigint AS distinct_sources,
                  COUNT(DISTINCT category)
                    FILTER (WHERE category IS NOT NULL)::bigint AS distinct_categories,
                  COUNT(*) FILTER (WHERE value_decimal IS NULL)::bigint AS null_value_decimal_count,
                  COALESCE(SUM(value_decimal), 0)::numeric(18, 6) AS sum_value_decimal,
                  COALESCE(AVG(value_decimal), 0)::numeric(18, 6) AS avg_value_decimal
                FROM clean.clean_records
                WHERE source = :dataset_key
                """
            ),
            {"dataset_key": dataset_key},
        )
        .mappings()
        .one()
    )
    return result


def _build_rows(
    *,
    feature_defs: list[FeatureDef],
    numeric_values: Mapping[str, Decimal],
    run_id: uuid.UUID,
    dataset_key: str,
) -> list[dict[str, Any]]:
    computed_at = datetime.now(UTC)
    rows: list[dict[str, Any]] = []

    for feature_def in feature_defs:
        numeric_value = numeric_values.get(feature_def.name) if feature_def.dtype == "num" else None
        rows.append(
            {
                "run_id": run_id,
                "dataset_key": dataset_key,
                "feature_name": feature_def.name,
                "feature_value_num": numeric_value,
                "feature_value_text": None,
                "feature_value_json": None,
                "computed_at": computed_at,
            }
        )

    return rows


def compute_features_for_run(
    session: Session,
    run_id: uuid.UUID | str,
    dataset_key: str,
) -> list[FeatureValue]:
    resolved_run_id = run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))
    feature_defs = get_feature_defs()

    aggregates = _fetch_clean_aggregates(session, dataset_key=dataset_key)
    numeric_values = compute_numeric_features(aggregates)
    rows = _build_rows(
        feature_defs=feature_defs,
        numeric_values=numeric_values,
        run_id=resolved_run_id,
        dataset_key=dataset_key,
    )

    if rows:
        stmt = pg_insert(FeatureValue.__table__).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["run_id", "dataset_key", "feature_name"],
            set_={
                "feature_value_num": stmt.excluded.feature_value_num,
                "feature_value_text": stmt.excluded.feature_value_text,
                "feature_value_json": stmt.excluded.feature_value_json,
                "computed_at": stmt.excluded.computed_at,
            },
        )
        session.execute(stmt)
        session.flush()

    persisted_stmt = (
        sa.select(FeatureValue)
        .where(FeatureValue.run_id == resolved_run_id, FeatureValue.dataset_key == dataset_key)
        .order_by(FeatureValue.feature_name.asc())
    )
    return list(session.scalars(persisted_stmt).all())
