# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas.decisions import DecisionEnvelope, DecisionListResponse
from app.db.session import get_db
from app.decision_api.service import (
    get_decision_by_run_id as get_decision_by_run_id_service,
)
from app.decision_api.service import (
    get_latest_decision as get_latest_decision_service,
)
from app.decision_api.service import (
    list_decisions as list_decisions_service,
)

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("/latest", response_model=DecisionEnvelope)
def get_latest_decision(db: Session = Depends(get_db)):
    item = get_latest_decision_service(db)
    if item is None:
        raise HTTPException(status_code=404, detail="No decisions yet")
    return item


def _get_decision_or_404(run_id: UUID, db: Session) -> DecisionEnvelope:
    item = get_decision_by_run_id_service(db, run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return item


@router.get("", response_model=DecisionListResponse)
def list_decisions(
    db: Session = Depends(get_db),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if from_ is not None and to is not None and from_ > to:
        raise HTTPException(status_code=400, detail="'from' must be less than or equal to 'to'")

    items, total_count = list_decisions_service(
        db,
        from_dt=from_,
        to_dt=to,
        limit=limit,
        offset=offset,
    )

    return DecisionListResponse(
        items=items,
        count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/by-run/{run_id}", response_model=DecisionEnvelope)
def get_decision_by_run_id_alias(run_id: UUID, db: Session = Depends(get_db)):
    return _get_decision_or_404(run_id, db)


@router.get("/{run_id}", response_model=DecisionEnvelope)
def get_decision_by_run_id(run_id: UUID, db: Session = Depends(get_db)):
    return _get_decision_or_404(run_id, db)
