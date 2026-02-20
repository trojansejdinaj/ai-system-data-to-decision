from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.models import Decision, DecisionOutput
from app.decision_policy.policy_v0 import DecisionResult


def write_decision(
    db_session: Session,
    run_id: uuid.UUID | str,
    result: DecisionResult,
) -> Decision:
    resolved_run_id = run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))

    existing = db_session.scalar(sa.select(Decision).where(Decision.run_id == resolved_run_id))
    if existing is not None:
        db_session.delete(existing)
        db_session.flush()

    row = Decision(
        id=uuid.uuid4(),
        run_id=resolved_run_id,
        policy_version=result.policy_version,
        decision=result.decision,
        score=result.score,
        top_reason=result.top_reason,
        reasons=list(result.reasons),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def canonicalize_input_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical = _canonicalize_json_value(payload)
    if not isinstance(canonical, dict):
        raise TypeError("Decision input payload must canonicalize to an object")
    return canonical


def compute_input_hash(payload: Mapping[str, Any]) -> str:
    canonical = canonicalize_input_payload(payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def save_decision_output(
    db_session: Session,
    result: DecisionResult,
    input_payload: Mapping[str, Any],
    *,
    meta: Mapping[str, Any] | None = None,
) -> DecisionOutput:
    canonical_input = canonicalize_input_payload(input_payload)
    row = DecisionOutput(
        id=uuid.uuid4(),
        policy_version=result.policy_version,
        input_hash=compute_input_hash(canonical_input),
        decision=result.decision,
        score=result.score,
        reasons=list(result.reasons),
        input=dict(canonical_input),
        meta=dict(_canonicalize_json_value(meta or {})),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def _canonicalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return value

    if isinstance(value, Mapping):
        items = sorted(
            ((str(key), child) for key, child in value.items()),
            key=lambda pair: pair[0],
        )
        return {key: _canonicalize_json_value(child) for key, child in items}

    if isinstance(value, list | tuple):
        return [_canonicalize_json_value(child) for child in value]

    if isinstance(value, set):
        normalized = [_canonicalize_json_value(child) for child in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, datetime | date):
        return value.isoformat()

    return str(value)
