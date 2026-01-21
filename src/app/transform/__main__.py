from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import text

from app.db.session import SessionLocal
from app.observability.logging import get_logger
from app.observability.run_tracking import RunTracker

SQL_PATH = Path("src/app/transform/monthly_metrics.sql")


def main() -> None:
    logger = get_logger(__name__)
    with SessionLocal() as db:
        tracker = RunTracker(db, logger, pipeline="metrics", input_ref=str(SQL_PATH))
        try:
            with tracker.step("apply_sql", meta={"path": str(SQL_PATH)}):
                sql = SQL_PATH.read_text(encoding="utf-8")
                # Remove single-line comments
                sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
                # Split on semicolons and filter empty statements
                parts = [p.strip() for p in sql.split(";") if p.strip()]
                for stmt in parts:
                    db.execute(text(stmt))
                db.commit()
            tracker.succeed()
        except Exception as e:
            db.rollback()
            tracker.fail(e)
            raise


if __name__ == "__main__":
    main()
