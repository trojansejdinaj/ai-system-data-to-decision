"""add run metrics (and rename ended_at to finished_at)

Revision ID: c7d9e1f2a3b4
Revises: 21e36aec99be
Create Date: 2026-01-31

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c7d9e1f2a3b4"
down_revision = "21e36aec99be"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename ended_at -> finished_at
    op.alter_column(
        "pipeline_runs",
        "ended_at",
        new_column_name="finished_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    # Add nullable run metric columns
    op.add_column("pipeline_runs", sa.Column("records_in", sa.Integer(), nullable=True))
    op.add_column("pipeline_runs", sa.Column("records_out", sa.Integer(), nullable=True))
    op.add_column("pipeline_runs", sa.Column("error_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove added columns
    op.drop_column("pipeline_runs", "error_summary")
    op.drop_column("pipeline_runs", "records_out")
    op.drop_column("pipeline_runs", "records_in")

    # Rename finished_at -> ended_at
    op.alter_column(
        "pipeline_runs",
        "finished_at",
        new_column_name="ended_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
