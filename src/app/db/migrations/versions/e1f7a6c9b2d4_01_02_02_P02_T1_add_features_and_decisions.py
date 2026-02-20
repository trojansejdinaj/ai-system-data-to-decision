"""add feature_values and decisions tables

Revision ID: e1f7a6c9b2d4
Revises: c7d9e1f2a3b4
Create Date: 2026-02-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e1f7a6c9b2d4"
down_revision = "c7d9e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS features;")
    op.execute("CREATE SCHEMA IF NOT EXISTS decisions;")

    op.create_table(
        "feature_values",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("feature_value_num", postgresql.NUMERIC(18, 6), nullable=True),
        sa.Column("feature_value_text", sa.Text(), nullable=True),
        sa.Column("feature_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["run_id"], ["pipeline_runs.id"]),
        sa.UniqueConstraint(
            "run_id",
            "dataset_key",
            "feature_name",
            name="uq_feature_values_run_dataset_feature_name",
        ),
        schema="features",
    )
    op.create_index(
        "ix_feature_values_run_id",
        "feature_values",
        ["run_id"],
        schema="features",
    )
    op.create_index(
        "ix_feature_values_dataset_key",
        "feature_values",
        ["dataset_key"],
        schema="features",
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("score", postgresql.NUMERIC(18, 6), nullable=True),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["run_id"], ["pipeline_runs.id"]),
        sa.UniqueConstraint("run_id", "policy_version", name="uq_decisions_run_policy_version"),
        schema="decisions",
    )
    op.create_index(
        "ix_decisions_run_id",
        "decisions",
        ["run_id"],
        schema="decisions",
    )


def downgrade() -> None:
    op.drop_index("ix_decisions_run_id", table_name="decisions", schema="decisions")
    op.drop_table("decisions", schema="decisions")

    op.drop_index("ix_feature_values_dataset_key", table_name="feature_values", schema="features")
    op.drop_index("ix_feature_values_run_id", table_name="feature_values", schema="features")
    op.drop_table("feature_values", schema="features")

    op.execute("DROP SCHEMA IF EXISTS decisions;")
    op.execute("DROP SCHEMA IF EXISTS features;")
