"""create public decisions table for policy v0

Revision ID: b4d6e8f9a1c2
Revises: e1f7a6c9b2d4
Create Date: 2026-02-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b4d6e8f9a1c2"
down_revision = "e1f7a6c9b2d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("policy_hash", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "explanation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("char_length(policy_hash) = 64", name="ck_decisions_policy_hash_len"),
        sa.ForeignKeyConstraint(["run_id"], ["pipeline_runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("run_id", name="uq_decisions_run_id"),
    )
    op.create_index("ix_decisions_run_id", "decisions", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_decisions_run_id", table_name="decisions")
    op.drop_table("decisions")
