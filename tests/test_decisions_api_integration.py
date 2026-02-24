from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.models import Decision, PipelineRun
from app.db.session import SessionLocal
from app.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def _truncate_tables() -> None:
    with SessionLocal() as db:
        db.execute(text("TRUNCATE TABLE decisions, pipeline_runs CASCADE;"))
        db.commit()


def _insert_run_and_decision(*, created_at: datetime, score: int, decision_value: str) -> uuid.UUID:
    run_id = uuid.uuid4()
    with SessionLocal() as db:
        run = PipelineRun(
            id=run_id,
            pipeline="decision",
            status="succeeded",
            started_at=created_at - timedelta(seconds=2),
            finished_at=created_at - timedelta(seconds=1),
            records_in=10,
            records_out=1,
            meta={
                "explanation_json": {
                    "policy_version": "v0",
                    "score_end": score,
                }
            },
        )
        db.add(run)
        db.flush()

        db.add(
            Decision(
                run_id=run_id,
                policy_version="v0",
                decision=decision_value,
                score=score,
                top_reason="test_reason",
                reasons=["test_reason"],
                created_at=created_at,
            )
        )
        db.commit()

    return run_id


def test_decisions_latest_returns_latest_entry() -> None:
    _truncate_tables()
    now = datetime.now(UTC)

    _insert_run_and_decision(
        created_at=now - timedelta(hours=1),
        score=55,
        decision_value="review",
    )
    latest_run_id = _insert_run_and_decision(
        created_at=now,
        score=88,
        decision_value="approve",
    )

    response = client.get("/decisions/latest")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["decision"]["run_id"] == str(latest_run_id)
    assert body["decision"]["decision"] == "approve"
    assert body["decision"]["score"] == 88
    assert body["decision"]["policy_version"] == "v0"
    assert body["decision"]["reasons"] == ["test_reason"]
    assert body["decision"]["explanation_json"]["score_end"] == 88
    assert body["run_meta"]["status"] == "succeeded"
    assert body["run_meta"]["records_in"] == 10
    assert body["run_meta"]["records_out"] == 1


def test_decisions_list_supports_window_and_paging() -> None:
    _truncate_tables()
    now = datetime.now(UTC)

    _insert_run_and_decision(
        created_at=now - timedelta(days=2),
        score=42,
        decision_value="reject",
    )
    mid_run_id = _insert_run_and_decision(
        created_at=now - timedelta(days=1),
        score=60,
        decision_value="review",
    )
    latest_run_id = _insert_run_and_decision(
        created_at=now,
        score=81,
        decision_value="approve",
    )

    window_response = client.get(
        "/decisions",
        params={
            "from": (now - timedelta(days=1, minutes=1)).isoformat(),
            "to": (now + timedelta(minutes=1)).isoformat(),
        },
    )
    assert window_response.status_code == 200, window_response.text
    window_body = window_response.json()
    assert [row["decision"]["run_id"] for row in window_body["items"]] == [
        str(latest_run_id),
        str(mid_run_id),
    ]
    assert window_body["count"] == 2

    paged_response = client.get("/decisions", params={"limit": 1, "offset": 1})
    assert paged_response.status_code == 200, paged_response.text
    paged_body = paged_response.json()
    assert paged_body["count"] == 3
    assert paged_body["limit"] == 1
    assert paged_body["offset"] == 1
    assert len(paged_body["items"]) == 1
    assert paged_body["items"][0]["decision"]["run_id"] == str(mid_run_id)


def test_decisions_by_run_id_found_and_not_found() -> None:
    _truncate_tables()
    now = datetime.now(UTC)

    run_id = _insert_run_and_decision(
        created_at=now,
        score=73,
        decision_value="review",
    )

    found = client.get(f"/decisions/{run_id}")
    assert found.status_code == 200, found.text
    assert found.json()["decision"]["run_id"] == str(run_id)

    missing = client.get(f"/decisions/{uuid.uuid4()}")
    assert missing.status_code == 404
