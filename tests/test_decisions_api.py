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
                meta={
                    "explanation_json": {
                        "score_end": score,
                        "rule_hits": [],
                    }
                },
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


def test_get_latest_returns_newest(client: TestClient) -> None:
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
    body = response.json()

    assert body["decision"]["run_id"] == str(newest_run_id)
    assert body["decision"]["decision"] == "approve"
    assert body["decision"]["score"] == 90


def test_get_by_run_id_returns_matching_payload(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    created_at = datetime(2026, 2, 2, 10, 0, tzinfo=UTC)
    run_id = _insert_run_and_decision(created_at=created_at, score=72, decision_value="review")

    response = client.get(f"/decisions/{run_id}")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["decision"]["run_id"] == str(run_id)
    assert body["decision"]["policy_version"] == "v0"
    assert body["decision"]["reasons"] == ["fixed_reason"]
    assert body["run_meta"]["status"] == "succeeded"


def test_list_returns_paging_metadata(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    base = datetime(2026, 2, 3, 8, 0, tzinfo=UTC)
    _insert_run_and_decision(created_at=base, score=45, decision_value="reject")
    middle_run_id = _insert_run_and_decision(
        created_at=base + timedelta(hours=1),
        score=60,
        decision_value="review",
    )
    _insert_run_and_decision(
        created_at=base + timedelta(hours=2),
        score=88,
        decision_value="approve",
    )

    response = client.get("/decisions", params={"limit": 1, "offset": 1})
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["count"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["decision"]["run_id"] == str(middle_run_id)


def test_list_from_to_filters_correctly(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    old_time = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
    keep_1 = datetime(2026, 2, 5, 0, 0, tzinfo=UTC)
    keep_2 = datetime(2026, 2, 6, 0, 0, tzinfo=UTC)

    _insert_run_and_decision(created_at=old_time, score=35, decision_value="reject")
    keep_1_run_id = _insert_run_and_decision(created_at=keep_1, score=65, decision_value="review")
    keep_2_run_id = _insert_run_and_decision(created_at=keep_2, score=82, decision_value="approve")

    response = client.get(
        "/decisions",
        params={
            "from": datetime(2026, 2, 4, 0, 0, tzinfo=UTC).isoformat(),
            "to": datetime(2026, 2, 7, 0, 0, tzinfo=UTC).isoformat(),
            "limit": 10,
            "offset": 0,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    returned_ids = [item["decision"]["run_id"] for item in body["items"]]
    assert returned_ids == [str(keep_2_run_id), str(keep_1_run_id)]
    assert body["count"] == 2


def test_404_when_latest_empty_and_unknown_run_id(client: TestClient) -> None:
    _ensure_db_available()
    _truncate_decision_tables()

    latest = client.get("/decisions/latest")
    assert latest.status_code == 404
    assert latest.json() == {"detail": "No decisions yet"}

    missing = client.get(f"/decisions/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Decision not found"}
