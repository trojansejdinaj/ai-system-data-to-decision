from __future__ import annotations

import os
from typing import Any

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.decision import (
    canonicalize_input_payload,
    compute_input_hash,
    save_decision_output,
)
from app.decision_policy.policy_v0 import (
    DecisionPolicy,
)

pytestmark = pytest.mark.integration


def _build_database_url_from_env() -> str | None:
    user = os.getenv("POSTGRES_USER")
    pwd = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "55432")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not (user and pwd and db):
        return None

    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"


def _db_engine():
    database_url = (
        os.getenv("DATABASE_URL") or os.getenv("DB_URL") or _build_database_url_from_env()
    )
    if not database_url:
        pytest.skip(
            "No DATABASE_URL/DB_URL and missing POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB; "
            "export env or load .env before running integration tests."
        )
    return create_engine(database_url, future=True)


def _table_exists(engine, table_name: str) -> bool:
    query = text("SELECT to_regclass(:table_name) IS NOT NULL")
    with engine.connect() as conn:
        return bool(conn.execute(query, {"table_name": table_name}).scalar())


def test_save_decision_output_persists_policy_version() -> None:
    engine = _db_engine()

    if not _table_exists(engine, "decision_outputs"):
        pytest.skip("decision_outputs table not found. Did you run migrations (make migrate)?")

    policy = DecisionPolicy(policy_version="v-test")
    input_payload: dict[str, Any] = {
        "total_clean_records": 12,
        "null_value_decimal_rate": 0.01,
        "distinct_categories": 3,
        "avg_value_decimal": 5.5,
    }
    result = policy.evaluate(input_payload)

    expected_hash = compute_input_hash(input_payload)
    expected_input = canonicalize_input_payload(input_payload)

    Session = sessionmaker(bind=engine, future=True)

    with Session() as db:
        saved = save_decision_output(
            db,
            result,
            input_payload,
            meta={"test_case": "test_save_decision_output_persists_policy_version"},
        )
        saved_id = saved.id

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT id, policy_version, input_hash, decision, score, reasons, input, meta
                    FROM decision_outputs
                    WHERE id = :id
                    """
                ),
                {"id": saved_id},
            )
            .mappings()
            .first()
        )

    assert row is not None
    assert row["policy_version"] == "v-test"
    assert row["input_hash"] == expected_hash
    assert row["decision"] == result.decision
    assert row["score"] == result.score
    assert row["reasons"] == result.reasons
    assert row["input"] == expected_input
    assert row["meta"]["test_case"] == "test_save_decision_output_persists_policy_version"
