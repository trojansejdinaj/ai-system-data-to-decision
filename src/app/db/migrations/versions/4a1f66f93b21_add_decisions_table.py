"""add decisions table

Revision ID: 4a1f66f93b21
Revises: 9f2b4a6c8d10
Create Date: 2026-02-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "4a1f66f93b21"
down_revision = "9f2b4a6c8d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("decisions", sa.Column("top_reason", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE decisions
        SET top_reason = COALESCE(NULLIF(reasons->>0, ''), 'no_reason_recorded')
        WHERE top_reason IS NULL
        """
    )
    op.alter_column("decisions", "top_reason", nullable=False)

    op.alter_column("decisions", "policy_version", type_=sa.String(length=50))
    op.alter_column("decisions", "decision", type_=sa.String(length=20))

    op.drop_constraint("ck_decisions_policy_hash_len", "decisions", type_="check")
    op.drop_constraint("uq_decisions_run_id", "decisions", type_="unique")

    op.drop_column("decisions", "policy_hash")
    op.drop_column("decisions", "explanation_json")

    op.create_check_constraint(
        "ck_decisions_score_range", "decisions", "score >= 0 AND score <= 100"
    )
    op.create_index(
        "ix_decisions_policy_version_decision",
        "decisions",
        ["policy_version", "decision"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_decisions_policy_version_decision", table_name="decisions")
    op.drop_constraint("ck_decisions_score_range", "decisions", type_="check")

    op.add_column(
        "decisions",
        sa.Column(
            "explanation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "decisions",
        sa.Column(
            "policy_hash",
            sa.Text(),
            nullable=False,
            server_default=sa.text("repeat('0', 64)"),
        ),
    )

    op.create_check_constraint(
        "ck_decisions_policy_hash_len",
        "decisions",
        "char_length(policy_hash) = 64",
    )
    op.create_unique_constraint("uq_decisions_run_id", "decisions", ["run_id"])

    op.alter_column("decisions", "decision", type_=sa.Text())
    op.alter_column("decisions", "policy_version", type_=sa.Text())

    op.drop_column("decisions", "top_reason")
