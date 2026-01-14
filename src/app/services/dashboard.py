from __future__ import annotations

from datetime import date
from typing import Literal

from sqlalchemy import text
from sqlalchemy.engine import Connection

Metric = Literal[
    "total_records",
    "distinct_records",
    "distinct_source_ids",
    "distinct_sources",
    "distinct_categories",
]
Granularity = Literal["day", "week", "month"]


def fetch_monthly_summary(conn: Connection, start: date | None, end: date | None):
    sql = """
    SELECT
      month_start,
      total_records,
      distinct_records,
      distinct_source_ids,
      distinct_sources,
      distinct_categories
    FROM summary.monthly_metrics
    WHERE (CAST(:start AS date) IS NULL OR month_start >= CAST(:start AS date))
      AND (CAST(:end AS date) IS NULL OR month_start < CAST(:end AS date))
    ORDER BY month_start;
    """
    return conn.execute(text(sql), {"start": start, "end": end}).mappings().all()


def fetch_trend(conn: Connection, start: date, end: date, granularity: Granularity, metric: Metric):
    # Trend view is powered by summary.daily_metrics (created in Week 06 migration)
    # We re-bucket daily into day/week/month based on requested granularity.
    if granularity == "day":
        bucket = "day_date"
    elif granularity == "week":
        bucket = "date_trunc('week', day_date)::date"
    else:
        bucket = "date_trunc('month', day_date)::date"

    sql = f"""
    SELECT
      {bucket} AS bucket_start,
      SUM({metric})::bigint AS value
    FROM summary.daily_metrics
    WHERE day_date >= :start
      AND day_date < :end
    GROUP BY 1
    ORDER BY 1;
    """
    return conn.execute(text(sql), {"start": start, "end": end}).mappings().all()
