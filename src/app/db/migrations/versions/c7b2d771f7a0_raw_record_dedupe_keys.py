"""raw record dedupe keys

Revision ID: c7b2d771f7a0
Revises: 3d1e14bb5580
Create Date: 2026-01-26 00:00:00.000000

"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7b2d771f7a0"
down_revision: str | Sequence[str] | None = "3d1e14bb5580"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _parse_event_time(v: Any) -> datetime:
    if v is None:
        raise ValueError("event_time is required")

    if isinstance(v, datetime):
        dt = v
    else:
        s = str(v).strip()
        if not s:
            raise ValueError("event_time is required")
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _norm_str(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _compute_hash(source_id: str, event_dt: datetime, category: str, value: str) -> str:
    key = {
        "source_id": source_id,
        "event_time": event_dt.isoformat(),
        "category": category,
        "value": value,
    }
    encoded = json.dumps(key, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def upgrade() -> None:
    # 1) Add new columns (nullable first so we can backfill)
    op.add_column("raw_records", sa.Column("source", sa.String(length=50), nullable=True))
    op.add_column("raw_records", sa.Column("record_hash", sa.String(length=64), nullable=True))
    op.add_column("raw_records", sa.Column("source_id", sa.String(length=100), nullable=True))
    op.add_column("raw_records", sa.Column("event_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("raw_records", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("raw_records", sa.Column("value", sa.Text(), nullable=True))

    # 2) Backfill from existing rows (join ingest_runs for source)
    bind = op.get_bind()

    rows = bind.execute(
        sa.text(
            """
            SELECT rr.id, rr.payload, ir.source
            FROM raw_records rr
            JOIN ingest_runs ir ON ir.id = rr.run_id
            """
        )
    ).fetchall()

    for row in rows:
        raw_id = row[0]
        payload = row[1]
        source = row[2]

        if isinstance(payload, str):
            payload_dict = json.loads(payload)
        else:
            payload_dict = dict(payload)

        source_id = _norm_str(payload_dict.get("source_id"))
        category = _norm_str(payload_dict.get("category")).lower()
        value = _norm_str(payload_dict.get("value"))
        event_dt = _parse_event_time(payload_dict.get("event_time"))
        record_hash = _compute_hash(source_id, event_dt, category, value)

        bind.execute(
            sa.text(
                """
                UPDATE raw_records
                SET source = :source,
                    record_hash = :record_hash,
                    source_id = :source_id,
                    event_time = :event_time,
                    category = :category,
                    value = :value
                WHERE id = :id
                """
            ),
            {
                "id": raw_id,
                "source": source,
                "record_hash": record_hash,
                "source_id": source_id,
                "event_time": event_dt,
                "category": category,
                "value": value,
            },
        )

    # 3) Enforce NOT NULL (safe after backfill)
    op.alter_column("raw_records", "source", nullable=False)
    op.alter_column("raw_records", "record_hash", nullable=False)
    op.alter_column("raw_records", "source_id", nullable=False)
    op.alter_column("raw_records", "event_time", nullable=False)
    op.alter_column("raw_records", "category", nullable=False)
    op.alter_column("raw_records", "value", nullable=False)

    # 4) Add unique constraint + indexes for performance
    op.create_unique_constraint(
        "uq_raw_records_source_record_hash",
        "raw_records",
        ["source", "record_hash"],
    )

    op.create_index("ix_raw_records_record_hash", "raw_records", ["record_hash"], unique=False)
    op.create_index("ix_raw_records_source", "raw_records", ["source"], unique=False)
    op.create_index(
        "ix_raw_records_source_event_time",
        "raw_records",
        ["source", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_raw_records_source_source_id",
        "raw_records",
        ["source", "source_id"],
        unique=False,
    )
    op.create_index("ix_raw_records_category", "raw_records", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_records_category", table_name="raw_records")
    op.drop_index("ix_raw_records_source_source_id", table_name="raw_records")
    op.drop_index("ix_raw_records_source_event_time", table_name="raw_records")
    op.drop_index("ix_raw_records_source", table_name="raw_records")
    op.drop_index("ix_raw_records_record_hash", table_name="raw_records")

    op.drop_constraint("uq_raw_records_source_record_hash", "raw_records", type_="unique")

    op.drop_column("raw_records", "value")
    op.drop_column("raw_records", "category")
    op.drop_column("raw_records", "event_time")
    op.drop_column("raw_records", "source_id")
    op.drop_column("raw_records", "record_hash")
    op.drop_column("raw_records", "source")
