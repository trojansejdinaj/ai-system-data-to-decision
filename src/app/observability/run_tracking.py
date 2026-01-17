# app/observability/run_tracking.py
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import PipelineRun


@dataclass
class StepInfo:
    step: str
    status: str
    duration_ms: int
    meta: dict = field(default_factory=dict)


class StepTimer:
    def __init__(self, tracker: RunTracker, step: str, meta: dict | None = None):
        self.tracker = tracker
        self.step = step
        self.meta = meta or {}
        self._t0 = 0.0

    def __enter__(self):
        self._t0 = time.perf_counter()
        self.tracker.log("step_started", step=self.step, status="running", meta=self.meta)
        return self

    def __exit__(self, exc_type, exc, tb):
        dt_ms = int((time.perf_counter() - self._t0) * 1000)

        if exc is not None:
            self.tracker.steps.append(
                StepInfo(self.step, "failed", dt_ms, {"error": str(exc), **self.meta})
            )
            self.tracker.log(
                "step_failed",
                step=self.step,
                status="failed",
                duration_ms=dt_ms,
                error_type=getattr(exc_type, "__name__", "Exception"),
                error_message=str(exc),
            )
            return False

        self.tracker.steps.append(StepInfo(self.step, "ok", dt_ms, self.meta))
        self.tracker.log("step_succeeded", step=self.step, status="ok", duration_ms=dt_ms)
        return False


class RunTracker:
    def __init__(
        self,
        db: Session,
        logger,
        pipeline: str,
        input_ref: str | None = None,
        meta: dict | None = None,
    ):
        self.db = db
        self.logger = logger
        self.pipeline = pipeline
        self.input_ref = input_ref
        self.meta = meta or {}

        self.run_id = uuid.uuid4()
        self.started_at = datetime.now(UTC)
        self.steps: list[StepInfo] = []

        self.row = PipelineRun(
            id=self.run_id,
            pipeline=pipeline,
            status="running",
            started_at=self.started_at,
            input_ref=input_ref,
            meta=self.meta,
            steps=[],
        )
        db.add(self.row)
        db.flush()

        self.log("run_started", status="running")

    def step(self, name: str, meta: dict | None = None) -> StepTimer:
        return StepTimer(self, name, meta=meta)

    def log(self, message: str, **fields):
        self.logger.info(
            message,
            extra={
                "run_id": str(self.run_id),
                "pipeline": self.pipeline,
                **fields,
            },
        )

    def succeed(self):
        ended_at = datetime.now(UTC)
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)

        self.row.status = "succeeded"
        self.row.ended_at = ended_at
        self.row.duration_ms = duration_ms
        self.row.steps = [s.__dict__ for s in self.steps]
        self.db.add(self.row)
        self.db.commit()

        self.log("run_succeeded", status="succeeded", duration_ms=duration_ms)

    def fail(self, exc: Exception):
        ended_at = datetime.now(UTC)
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)

        # IMPORTANT: rollback whatever work failed, but still persist run status
        self.db.rollback()

        self.row.status = "failed"
        self.row.ended_at = ended_at
        self.row.duration_ms = duration_ms
        self.row.error_type = type(exc).__name__
        self.row.error_message = str(exc)
        self.row.steps = [s.__dict__ for s in self.steps]
        self.db.add(self.row)
        self.db.commit()

        self.log(
            "run_failed",
            status="failed",
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
