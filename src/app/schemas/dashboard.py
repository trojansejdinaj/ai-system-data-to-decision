from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class MonthlySummaryRow(BaseModel):
    month_start: date
    total_records: int
    distinct_records: int
    distinct_source_ids: int
    distinct_sources: int
    distinct_categories: int


class TrendPoint(BaseModel):
    bucket_start: date
    value: int = Field(..., description="Count for the bucket")


class TrendResponse(BaseModel):
    granularity: Literal["day", "week", "month"]
    metric: Literal[
        "total_records",
        "distinct_records",
        "distinct_source_ids",
        "distinct_sources",
        "distinct_categories",
    ]
    start: date
    end: date
    points: list[TrendPoint]
    note: str | None = None
