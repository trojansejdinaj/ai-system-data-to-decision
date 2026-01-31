from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.cleaning.pipeline import CleaningConfig, clean_row
from app.cleaning.rules import normalize_currency_to_decimal
from app.db.models import CleanRecord, RawRecord
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker


def refresh_clean_records(db: Session, *, limit: int = 5000) -> int:
    logger = get_logger(__name__)
    tracker = RunTracker(db, logger, pipeline="clean", input_ref=f"raw_records(limit={limit})")

    cfg = CleaningConfig(
        allowed_keys={"source_id", "event_time", "value", "category"},
        day_first=True,
        category_mapping={},
        outlier_rules={},
    )

    try:
        with tracker.step("fetch_raw_records", meta={"limit": limit}):
            raws = db.query(RawRecord).order_by(RawRecord.ingested_at.desc()).limit(limit).all()

        with tracker.step("upsert_clean_records", meta={"record_count": len(raws)}):
            now = datetime.now(UTC)
            rows = []
            for r in raws:
                cleaned = clean_row(dict(r.payload), cfg)
                value_text = None if cleaned.get("value") is None else str(cleaned.get("value"))
                value_decimal = normalize_currency_to_decimal(cleaned.get("value"))

                rows.append(
                    {
                        "id": uuid.uuid4(),
                        "raw_id": r.id,
                        "run_id": r.run_id,
                        "source": r.source,
                        "record_hash": r.record_hash,
                        "source_id": r.source_id,
                        "event_time": r.event_time,
                        "category": cleaned.get("category")
                        if cleaned.get("category") is not None
                        else r.category,
                        "value_text": value_text,
                        "value_decimal": value_decimal,
                        "payload_clean": cleaned,
                        "cleaned_at": now,
                    }
                )

            if rows:
                stmt = pg_insert(CleanRecord.__table__).values(rows)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["source", "record_hash"],
                    set_={
                        "raw_id": stmt.excluded.raw_id,
                        "run_id": stmt.excluded.run_id,
                        "source_id": stmt.excluded.source_id,
                        "event_time": stmt.excluded.event_time,
                        "category": stmt.excluded.category,
                        "value_text": stmt.excluded.value_text,
                        "value_decimal": stmt.excluded.value_decimal,
                        "payload_clean": stmt.excluded.payload_clean,
                        "cleaned_at": stmt.excluded.cleaned_at,
                    },
                )
                db.execute(stmt)

        db.commit()
        total_clean = db.query(func.count(CleanRecord.id)).scalar() or 0
        tracker.row.meta = {**(tracker.row.meta or {}), "total_clean": int(total_clean)}
        # wire counts: input = raws scanned, output = total_clean
        try:
            tracker.set_counts(records_in=len(raws), records_out=int(total_clean))
        except Exception:
            pass
        tracker.succeed()
        return int(total_clean)

    except Exception as e:
        db.rollback()
        tracker.fail(e)
        raise
