# tests/test_run_tracking_unit.py
from __future__ import annotations

import io
import json
import logging

import pytest

from app.observability.logging import JsonFormatter
from app.observability.run_tracking import RunTracker


class FakeSession:
    """Unit-test DB session: no real database, just records calls."""

    def __init__(self):
        self.added = []
        self.flushed = 0
        self.committed = 0
        self.rolled_back = 0

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed += 1

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1


def make_json_logger(name: str = "test") -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(stream)
    h.setFormatter(JsonFormatter())
    logger.addHandler(h)
    logger.propagate = False
    return logger, stream


def parse_lines(stream: io.StringIO) -> list[dict]:
    stream.seek(0)
    lines = [ln.strip() for ln in stream.getvalue().splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


def test_run_tracker_creates_running_row_and_logs_run_started():
    db = FakeSession()
    logger, stream = make_json_logger()

    tracker = RunTracker(db=db, logger=logger, pipeline="flags", input_ref="sample.csv")

    assert tracker.row.status == "running"
    assert tracker.row.pipeline == "flags"
    assert db.flushed == 1

    events = parse_lines(stream)
    assert any(e["message"] == "run_started" for e in events)
    assert all("run_id" in e for e in events if e["message"] == "run_started")


def test_step_timer_records_success_step_and_duration():
    db = FakeSession()
    logger, stream = make_json_logger()

    tracker = RunTracker(db=db, logger=logger, pipeline="flags")
    with tracker.step("fetch_raw"):
        pass

    assert len(tracker.steps) == 1
    step = tracker.steps[0]
    assert step.step == "fetch_raw"
    assert step.status == "ok"
    assert step.duration_ms >= 0

    events = parse_lines(stream)
    assert any(e["message"] == "step_started" and e["step"] == "fetch_raw" for e in events)
    assert any(e["message"] == "step_succeeded" and e["step"] == "fetch_raw" for e in events)


def test_run_tracker_fail_marks_failed_and_rolls_back_and_persists_error():
    db = FakeSession()
    logger, stream = make_json_logger()

    tracker = RunTracker(db=db, logger=logger, pipeline="flags")

    with pytest.raises(ValueError):
        with tracker.step("write_report"):
            raise ValueError("boom")

    # the step is recorded as failed
    assert tracker.steps[-1].status == "failed"

    # when we explicitly fail the run, it rolls back then commits status
    tracker.fail(ValueError("boom"))
    assert db.rolled_back == 1
    assert db.committed == 1

    assert tracker.row.status == "failed"
    assert tracker.row.error_type == "ValueError"
    assert "boom" in (tracker.row.error_message or "")

    events = parse_lines(stream)
    assert any(e["message"] == "run_failed" for e in events)
    assert any(e["message"] == "step_failed" and e["step"] == "write_report" for e in events)
