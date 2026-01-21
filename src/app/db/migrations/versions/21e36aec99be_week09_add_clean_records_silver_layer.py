from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "21e36aec99be"
down_revision = "f1a2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS clean;")

    op.create_table(
        "clean_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("raw_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_decimal", postgresql.NUMERIC(18, 4), nullable=True),
        sa.Column("payload_clean", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cleaned_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "record_hash", name="uq_clean_records_source_record_hash"),
        schema="clean",
    )

    op.create_index(
        "ix_clean_records_source_event_time",
        "clean_records",
        ["source", "event_time"],
        schema="clean",
    )
    op.create_index(
        "ix_clean_records_category",
        "clean_records",
        ["category"],
        schema="clean",
    )


def downgrade() -> None:
    op.drop_index("ix_clean_records_category", table_name="clean_records", schema="clean")
    op.drop_index("ix_clean_records_source_event_time", table_name="clean_records", schema="clean")
    op.drop_table("clean_records", schema="clean")
    op.execute("DROP SCHEMA IF EXISTS clean;")
