from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DecisionOut(BaseModel):
    run_id: str
    decision: str
    score: float | int
    reasons: list[str]
    explanation_json: dict[str, Any]
    policy_version: str
    policy_hash: str | None = None
    decided_at: datetime


class RunMetaOut(BaseModel):
    run_started_at: datetime | None = None
    run_finished_at: datetime | None = None
    records_in: int | None = None
    records_out: int | None = None
    status: str | None = None


class DecisionEnvelope(BaseModel):
    decision: DecisionOut
    run_meta: RunMetaOut


class DecisionListResponse(BaseModel):
    items: list[DecisionEnvelope]
    count: int
    limit: int
    offset: int
