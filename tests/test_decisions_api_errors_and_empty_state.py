from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.models import Decision, PipelineRun
from app.db.session import SessionLocal
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _ensure_db_available() -> None:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Database not available for integration API tests")


def _truncate_decision_tables() -> None:
    with SessionLocal() as db:
        db.execute(text("TRUNCATE TABLE decisions, pipeline_runs CASCADE;"))
        db.commit()


def _insert_run_and_decision(*, created_at: datetime, score: int, decision_value: str) -> uuid.UUID:
    run_id = uuid.uuid4()
    with SessionLocal() as db:
        db.add(
            PipelineRun(
                id=run_id,
                pipeline="decision",
                status="succeeded",
                started_at=created_at - timedelta(minutes=5),
                finished_at=created_at - timedelta(minutes=1),
                records_in=10,
                records_out=1,
                meta={"explanation_json": {"score_end": score}},
            )
        )
        db.flush()
        db.add(
            Decision(
                run_id=run_id,
                policy_version="v0",
                decision=decision_value,
                score=score,
                top_reason="fixed_reason",
                reasons=["fixed_reason"],
                created_at=created_at,
            )
        )
        db.commit()
    return run_id


def test_decisions_latest_empty_state_returns_404(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    response = client.get("/decisions/latest")
    assert response.status_code == 404
    assert response.json() == {"detail": "No decisions yet"}


def test_decisions_latest_happy_path_returns_latest(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    base = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)
    _insert_run_and_decision(created_at=base, score=55, decision_value="review")
    newest_run_id = _insert_run_and_decision(
        created_at=base + timedelta(hours=1),
        score=90,
        decision_value="approve",
    )

    response = client.get("/decisions/latest")
    assert response.status_code == 200, response.text
    assert response.json()["decision"]["run_id"] == str(newest_run_id)


def test_decision_by_run_id_not_found_returns_404(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    response = client.get(f"/decisions/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Decision not found"}

    alias_response = client.get(f"/decisions/by-run/{uuid.uuid4()}")
    assert alias_response.status_code == 404
    assert alias_response.json() == {"detail": "Decision not found"}
