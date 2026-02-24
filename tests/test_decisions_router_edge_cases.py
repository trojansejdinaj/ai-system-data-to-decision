from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_decisions_list_from_gt_to_returns_400() -> None:
    response = client.get(
        "/decisions",
        params={
            "from": "2026-02-03T00:00:00+00:00",
            "to": "2026-02-02T00:00:00+00:00",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "'from' must be less than or equal to 'to'"}


def test_decisions_list_limit_bounds_enforced() -> None:
    low = client.get("/decisions", params={"limit": 0})
    assert low.status_code == 422

    high = client.get("/decisions", params={"limit": 201})
    assert high.status_code == 422


def test_decision_by_run_id_with_missing_pipeline_run(monkeypatch) -> None:
    from app.api.routers import decisions as decisions_router
    from app.api.schemas.decisions import DecisionEnvelope, DecisionOut, RunMetaOut

    run_id = "c5e3088f-cb6a-471d-9f95-b4420cf33f5f"

    def _fake_get_decision_by_run_id_service(db, rid):
        if str(rid) != run_id:
            return None
        return DecisionEnvelope(
            decision=DecisionOut(
                run_id=run_id,
                decision="review",
                score=55,
                reasons=["low volume"],
                explanation_json={"rule_hits": []},
                policy_version="v0",
                policy_hash=None,
                decided_at=datetime(2026, 2, 24, 12, 0, tzinfo=UTC),
            ),
            run_meta=RunMetaOut(
                run_started_at=None,
                run_finished_at=None,
                records_in=None,
                records_out=None,
                status=None,
            ),
        )

    monkeypatch.setattr(
        decisions_router,
        "get_decision_by_run_id_service",
        _fake_get_decision_by_run_id_service,
    )

    response = client.get(f"/decisions/{run_id}")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["decision"]["run_id"] == run_id
    assert body["run_meta"] == {
        "run_started_at": None,
        "run_finished_at": None,
        "records_in": None,
        "records_out": None,
        "status": None,
    }
