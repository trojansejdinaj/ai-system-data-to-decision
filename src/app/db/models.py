from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
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
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    records_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

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
        Index("ix_clean_records_run_id", "run_id"),
        {"schema": "clean"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_runs.id"), nullable=False
    )

    source: Mapped[str] = mapped_column(String(50), index=True)
    record_hash: Mapped[str] = mapped_column(String(64), index=True)

    source_id: Mapped[str] = mapped_column(String(100))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_decimal: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 4), nullable=True)

    payload_clean: Mapped[dict] = mapped_column(JSONB, default=dict)
    cleaned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FeatureValue(Base):
    __tablename__ = "feature_values"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "dataset_key",
            "feature_name",
            name="uq_feature_values_run_dataset_feature_name",
        ),
        Index("ix_feature_values_run_id", "run_id"),
        Index("ix_feature_values_dataset_key", "dataset_key"),
        {"schema": "features"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_runs.id"), nullable=False
    )
    dataset_key: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value_num: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 6), nullable=True)
    feature_value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_decisions_score_range"),
        Index("ix_decisions_policy_version_decision", "policy_version", "decision"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    top_reason: Mapped[str] = mapped_column(Text, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DecisionOutput(Base):
    __tablename__ = "decision_outputs"
    __table_args__ = (
        CheckConstraint(
            "char_length(input_hash) = 64",
            name="ck_decision_outputs_input_hash_len",
        ),
        Index("ix_decision_outputs_policy_version", "policy_version"),
        Index("ix_decision_outputs_input_hash", "input_hash"),
        Index("ix_decision_outputs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    input: Mapped[dict] = mapped_column(JSONB, default=dict)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
