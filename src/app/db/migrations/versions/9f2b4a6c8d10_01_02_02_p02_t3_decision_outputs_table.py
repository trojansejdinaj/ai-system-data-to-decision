"""create decision_outputs table for deterministic persisted outputs

Revision ID: 9f2b4a6c8d10
Revises: b4d6e8f9a1c2
Create Date: 2026-02-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "9f2b4a6c8d10"
down_revision = "b4d6e8f9a1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "input",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "char_length(input_hash) = 64",
            name="ck_decision_outputs_input_hash_len",
        ),
    )
    op.create_index(
        "ix_decision_outputs_policy_version",
        "decision_outputs",
        ["policy_version"],
    )
    op.create_index("ix_decision_outputs_input_hash", "decision_outputs", ["input_hash"])
    op.create_index("ix_decision_outputs_created_at", "decision_outputs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_decision_outputs_created_at", table_name="decision_outputs")
    op.drop_index("ix_decision_outputs_input_hash", table_name="decision_outputs")
    op.drop_index("ix_decision_outputs_policy_version", table_name="decision_outputs")
    op.drop_table("decision_outputs")
