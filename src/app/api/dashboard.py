from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.schemas.dashboard import MonthlySummaryRow, TrendResponse
from app.services.dashboard import fetch_monthly_summary, fetch_trend

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# If you already have a DB dependency (recommended), replace this with your existing one.
def get_engine() -> Engine:
    # expects DATABASE_URL in env
    import os

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return create_engine(url, pool_pre_ping=True)


@router.get("/monthly", response_model=list[MonthlySummaryRow])
def dashboard_monthly(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    engine: Engine = Depends(get_engine),
):
    with engine.begin() as conn:
        rows = fetch_monthly_summary(conn, start=start, end=end)
        return [MonthlySummaryRow(**r) for r in rows]


@router.get("/trend", response_model=TrendResponse)
def dashboard_trend(
    start: date = Query(..., description="Inclusive start date"),
    end: date = Query(..., description="Exclusive end date"),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    metric: Literal[
        "total_records",
        "distinct_records",
        "distinct_source_ids",
        "distinct_sources",
        "distinct_categories",
    ] = Query(default="total_records"),
    engine: Engine = Depends(get_engine),
):
    with engine.begin() as conn:
        points = fetch_trend(conn, start=start, end=end, granularity=granularity, metric=metric)

    return TrendResponse(
        granularity=granularity,
        metric=metric,
        start=start,
        end=end,
        points=[{"bucket_start": p["bucket_start"], "value": int(p["value"])} for p in points],
        note="Trend is aggregated from summary.daily_metrics (Week 06).",
    )
