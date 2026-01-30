"""week06 add monthly_metrics for dashboard

Revision ID: d991844d1931
Revises: eb012713281d
Create Date: 2026-01-14
"""

from __future__ import annotations

from alembic import op

revision = "d991844d1931"
down_revision = "eb012713281d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS summary;")

    # If an older VIEW exists (from earlier experiments), remove it
    op.execute("DROP VIEW IF EXISTS summary.monthly_metrics;")

    # ✅ THIS is where the table is created
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS summary.monthly_metrics (
          month_start date PRIMARY KEY,
          total_records bigint NOT NULL,
          distinct_records bigint NOT NULL,
          distinct_source_ids bigint NOT NULL,
          distinct_sources bigint NOT NULL,
          distinct_categories bigint NOT NULL
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_monthly_metrics_month_start
        ON summary.monthly_metrics (month_start);
        """
    )

    # backfill from raw_records (bucket by month)
    op.execute(
        """
        INSERT INTO summary.monthly_metrics (
          month_start,
          total_records,
          distinct_records,
          distinct_source_ids,
          distinct_sources,
          distinct_categories
        )
        SELECT
          date_trunc('month', event_time)::date AS month_start,
          count(*) AS total_records,
          count(DISTINCT (source, record_hash)) AS distinct_records,
          count(DISTINCT source_id) AS distinct_source_ids,
          count(DISTINCT source) AS distinct_sources,
          count(DISTINCT category) AS distinct_categories
        FROM public.raw_records
        GROUP BY 1
        ON CONFLICT (month_start) DO UPDATE SET
          total_records = EXCLUDED.total_records,
          distinct_records = EXCLUDED.distinct_records,
          distinct_source_ids = EXCLUDED.distinct_source_ids,
          distinct_sources = EXCLUDED.distinct_sources,
          distinct_categories = EXCLUDED.distinct_categories;
        """
    )


def downgrade() -> None:
    # make downgrade robust whether it’s a table or a view
    op.execute("DROP VIEW IF EXISTS summary.monthly_metrics;")
    op.execute("DROP TABLE IF EXISTS summary.monthly_metrics;")
