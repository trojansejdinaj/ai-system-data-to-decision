from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Timezone-aware UTC 'now' for SQLAlchemy defaults."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="started")
    files: Mapped[str] = mapped_column(Text)  # newline-separated filenames for now
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    records: Mapped[list[RawRecord]] = relationship(back_populates="run")


class RawRecord(Base):
    __tablename__ = "raw_records"

    # Dedupe rule: a raw record is uniquely identified per source by its stable record_hash.
    __table_args__ = (
        UniqueConstraint("source", "record_hash", name="uq_raw_records_source_record_hash"),
        Index("ix_raw_records_source_event_time", "source", "event_time"),
        Index("ix_raw_records_source_source_id", "source", "source_id"),
        Index("ix_raw_records_category", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingest_runs.id"),
        index=True,
    )

    # Denormalized keys for idempotency + query performance.
    source: Mapped[str] = mapped_column(String(50), index=True)
    record_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(100))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)

    row_num: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    run: Mapped[IngestRun] = relationship(back_populates="records")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    pipeline: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    input_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    steps: Mapped[list] = mapped_column(JSONB, default=list)

    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class CleanRecord(Base):
    __tablename__ = "clean_records"
    __table_args__ = (
        UniqueConstraint("source", "record_hash", name="uq_clean_records_source_record_hash"),
        Index("ix_clean_records_source_event_time", "source", "event_time"),
        Index("ix_clean_records_category", "category"),
        {"schema": "clean"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    source: Mapped[str] = mapped_column(String(50), index=True)
    record_hash: Mapped[str] = mapped_column(String(64), index=True)

    source_id: Mapped[str] = mapped_column(String(100))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_decimal: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 4), nullable=True)

    payload_clean: Mapped[dict] = mapped_column(JSONB, default=dict)
    cleaned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
