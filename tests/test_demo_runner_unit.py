from __future__ import annotations

from typing import Any

import pytest

from app.demo import __main__ as demo_main


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def info(self, message: str, **kwargs: Any) -> None:
        self.events.append((message, kwargs))


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = 0
        self.committed = 0
        self.rolled_back = 0
        self.closed = 0

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed += 1

    def commit(self) -> None:
        self.committed += 1

    def rollback(self) -> None:
        self.rolled_back += 1

    def close(self) -> None:
        self.closed += 1


def _latest_demo_row(fake_db: FakeSession):
    rows = [row for row in fake_db.added if getattr(row, "pipeline", None) == "demo"]
    assert rows
    return rows[-1]


def test_format_demo_summary_has_expected_block_shape() -> None:
    rendered = demo_main.format_demo_summary(
        run_id="abc-123",
        status="succeeded",
        duration_ms=87,
        records_in=20,
        records_out=10,
        decision="approve",
        score=90,
        top_reason="no_flags_detected",
    )

    lines = rendered.splitlines()
    assert lines[0] == "=" * demo_main.SUMMARY_WIDTH
    assert lines[1] == "DEMO SUMMARY"
    assert lines[2] == "-" * demo_main.SUMMARY_WIDTH
    assert lines[-1] == "=" * demo_main.SUMMARY_WIDTH

    assert "run_id      : abc-123" in rendered
    assert "status      : succeeded" in rendered
    assert "duration_ms : 87" in rendered
    assert "records_in  : 20" in rendered
    assert "records_out : 10" in rendered
    assert "decision    : approve" in rendered
    assert "score       : 90" in rendered
    assert "top_reason  : no_flags_detected" in rendered


def test_demo_fail_marks_failed_and_prints_summary_once(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_db = FakeSession()
    fake_logger = FakeLogger()

    monkeypatch.setattr(demo_main, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(demo_main, "get_logger", lambda _name: fake_logger)
    monkeypatch.setattr(demo_main, "_run_python_module", lambda _module, _args=(): None)
    monkeypatch.setattr(
        demo_main,
        "_run_decision_pipeline",
        lambda: {"decision": "review", "score": 70, "top_reason": "high_flag_density"},
    )
    monkeypatch.setattr(demo_main, "_collect_subpipeline_counts", lambda _db, _since: (20, 10))
    monkeypatch.setenv("DEMO_FAIL", "1")

    exit_code = demo_main.main()
    out = capsys.readouterr().out

    assert exit_code == 1
    assert out.count("DEMO SUMMARY") == 1

    row = _latest_demo_row(fake_db)
    assert row.status == "failed"
    assert row.error_summary is not None
    assert "Forced demo failure" in row.error_summary
    assert row.records_in == 20
    assert row.records_out == 10


def test_demo_success_calls_decision_pipeline_and_surfaces_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_db = FakeSession()
    fake_logger = FakeLogger()
    state = {"decision_called": 0}

    def _fake_run_decision_pipeline() -> dict[str, str | int]:
        state["decision_called"] += 1
        return {
            "decision": "review",
            "score": 70,
            "top_reason": "high_flag_density",
        }

    monkeypatch.setattr(demo_main, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(demo_main, "get_logger", lambda _name: fake_logger)
    monkeypatch.setattr(demo_main, "_run_python_module", lambda _module, _args=(): None)
    monkeypatch.setattr(demo_main, "_run_decision_pipeline", _fake_run_decision_pipeline)
    monkeypatch.setattr(demo_main, "_collect_subpipeline_counts", lambda _db, _since: (20, 10))
    monkeypatch.setattr(demo_main, "compute_features_for_run", lambda _db, _run_id, dataset_key: [])

    exit_code = demo_main.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert state["decision_called"] == 1
    assert out.count("DEMO SUMMARY") == 1
    assert "decision    : review" in out
    assert "score       : 70" in out
    assert "top_reason  : high_flag_density" in out

    row = _latest_demo_row(fake_db)
    assert row.status == "succeeded"
    assert row.meta["decision"] == "review"
    assert row.meta["score"] == 70
    assert row.meta["top_reason"] == "high_flag_density"
