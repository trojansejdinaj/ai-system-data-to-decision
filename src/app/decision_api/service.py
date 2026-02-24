from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.api.schemas.decisions import DecisionEnvelope, DecisionOut, RunMetaOut
from app.db.models import Decision, PipelineRun


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _to_envelope(decision: Decision, run: PipelineRun | None) -> DecisionEnvelope:
    run_meta = dict(run.meta or {}) if run is not None else {}
    explanation = run_meta.get("explanation_json", {})
    policy_hash = run_meta.get("policy_hash")

    return DecisionEnvelope(
        decision=DecisionOut(
            run_id=str(decision.run_id),
            decision=decision.decision,
            score=decision.score,
            reasons=list(decision.reasons or []),
            explanation_json=explanation if isinstance(explanation, dict) else {},
            policy_version=decision.policy_version,
            policy_hash=policy_hash if isinstance(policy_hash, str) else None,
            decided_at=_ensure_aware(decision.created_at),
        ),
        run_meta=RunMetaOut(
            run_started_at=_ensure_aware(run.started_at if run is not None else None),
            run_finished_at=_ensure_aware(run.finished_at if run is not None else None),
            records_in=run.records_in if run is not None else None,
            records_out=run.records_out if run is not None else None,
            status=run.status if run is not None else None,
        ),
    )


def _base_join_stmt() -> sa.Select:
    return sa.select(Decision, PipelineRun).outerjoin(
        PipelineRun,
        PipelineRun.id == Decision.run_id,
    )


def _apply_date_filters(
    stmt: sa.Select,
    *,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> sa.Select:
    if from_dt is not None:
        stmt = stmt.where(Decision.created_at >= from_dt)
    if to_dt is not None:
        stmt = stmt.where(Decision.created_at <= to_dt)
    return stmt


def _ordered(stmt: sa.Select) -> sa.Select:
    return stmt.order_by(Decision.created_at.desc(), Decision.id.desc())


def get_latest_decision(session: Session) -> DecisionEnvelope | None:
    row = session.execute(_ordered(_base_join_stmt()).limit(1)).first()
    if row is None:
        return None

    decision, run = row
    return _to_envelope(decision, run)


def list_decisions(
    session: Session,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DecisionEnvelope], int]:
    filtered = _apply_date_filters(_base_join_stmt(), from_dt=from_dt, to_dt=to_dt)

    total_count = int(
        session.execute(
            _apply_date_filters(sa.select(sa.func.count(Decision.id)), from_dt=from_dt, to_dt=to_dt)
        ).scalar_one()
    )

    rows = session.execute(_ordered(filtered).limit(limit).offset(offset)).all()
    items = [_to_envelope(decision, run) for decision, run in rows]
    return items, total_count


def get_decision_by_run_id(session: Session, run_id: UUID | str) -> DecisionEnvelope | None:
    resolved_run_id = run_id if isinstance(run_id, UUID) else UUID(str(run_id))
    row = session.execute(
        _ordered(_base_join_stmt()).where(Decision.run_id == resolved_run_id).limit(1)
    ).first()
    if row is None:
        return None

    decision, run = row
    return _to_envelope(decision, run)
