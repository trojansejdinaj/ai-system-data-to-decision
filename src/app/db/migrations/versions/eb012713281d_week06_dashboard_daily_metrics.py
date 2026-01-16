"""week06 dashboard daily metrics

Revision ID: eb012713281d
Revises: c7b2d771f7a0
Create Date: 2026-01-13 23:42:42.160251

"""

from alembic import op

# IMPORTANT:
# Update BASE_TABLE + TIME_COLUMN to match your real table/column that drives monthly metrics.
# This should be your "clean" or "core" table (not raw), with timestamp + category/source fields.
BASE_TABLE = "raw_records"
TIME_COLUMN = "event_time"

revision = "eb012713281d"
down_revision = "c7b2d771f7a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # schema for summaries
    op.execute("CREATE SCHEMA IF NOT EXISTS summary;")

    # daily rollup (powers Trend view)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS summary.daily_metrics (
          day_date date PRIMARY KEY,
          total_records bigint NOT NULL,
          distinct_records bigint NOT NULL,
          distinct_source_ids bigint NOT NULL,
          distinct_sources bigint NOT NULL,
          distinct_categories bigint NOT NULL
        );
        """
    )

    # helpful for filtering by ranges
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_daily_metrics_day_date ON summary.daily_metrics(day_date);"
    )

    # backfill
    op.execute(
        """
        INSERT INTO summary.daily_metrics (
          day_date, total_records, distinct_records, distinct_source_ids,
          distinct_sources, distinct_categories
        )
        SELECT
          date_trunc('day', event_time)::date AS day_date,
          count(*) AS total_records,
          count(DISTINCT (source, record_hash)) AS distinct_records,
          count(DISTINCT source_id) AS distinct_source_ids,
          count(DISTINCT source) AS distinct_sources,
          count(DISTINCT category) AS distinct_categories
        FROM public.raw_records
        GROUP BY 1
        ON CONFLICT (day_date) DO UPDATE SET
          total_records = EXCLUDED.total_records,
          distinct_records = EXCLUDED.distinct_records,
          distinct_source_ids = EXCLUDED.distinct_source_ids,
          distinct_sources = EXCLUDED.distinct_sources,
          distinct_categories = EXCLUDED.distinct_categories;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS summary.daily_metrics;")
