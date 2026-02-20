from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.models import Decision
from app.decisions.policy_v0 import DecisionResult


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
        policy_hash=result.policy_hash,
        decision=result.decision,
        score=result.score,
        reasons=list(result.reasons),
        explanation_json=dict(result.explanation_json),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row
