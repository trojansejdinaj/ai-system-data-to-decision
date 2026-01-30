from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import SessionLocal
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

from .engine import flag_records
from .report_csv import write_flag_report_csv

DEFAULT_QUERY = """
SELECT
  id,
  run_id,
  row_num,
  source,
  source_id,
  category,
  event_time,
  value,
  record_hash,
  ingested_at
FROM public.raw_records
ORDER BY ingested_at DESC
LIMIT :limit
"""


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL (or DB_URL) is required to generate the flags report.")

    limit = int(os.getenv("FLAGS_LIMIT", "5000"))
    out_path = Path(os.getenv("FLAGS_REPORT_PATH", "docs/assets/week-07/flags_report.csv"))

    logger = get_logger(__name__)
    db = SessionLocal()
    tracker = RunTracker(db, logger, pipeline="flags", input_ref=f"limit={limit}")

    try:
        with tracker.step("fetch_raw_records", meta={"limit": limit}):
            engine = create_engine(database_url)
            with engine.connect() as conn:
                rows = conn.execute(text(DEFAULT_QUERY), {"limit": limit}).mappings().all()
                records = [dict(r) for r in rows]

        with tracker.step("flag_records", meta={"record_count": len(records)}):
            now = datetime.now(UTC)
            flagged = flag_records(records, now=now)

        with tracker.step(
            "write_flag_report_csv",
            meta={"flagged_count": len(flagged), "output_path": out_path.as_posix()},
        ):
            out = write_flag_report_csv(flagged, out_path)

        tracker.succeed()

        print(f"Flagged records: {len(flagged)} / {len(records)}")
        print(f"Wrote: {out.as_posix()}")

        if flagged:
            print("Top 10 (severity | id | source_id | flags):")
            for fr in flagged[:10]:
                r = fr.record
                print(
                    f"  {fr.severity:3d} | {r.get('id', '')} | {r.get('source_id', '')} | "
                    f"{fr.flag_codes}"
                )

    except Exception as e:
        tracker.fail(e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
