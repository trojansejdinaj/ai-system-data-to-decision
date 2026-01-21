from __future__ import annotations

import os

from app.cleaning.service import refresh_clean_records
from app.db.session import SessionLocal

if __name__ == "__main__":
    limit = int(os.getenv("CLEAN_LIMIT", "5000"))
    with SessionLocal() as db:
        n = refresh_clean_records(db, limit=limit)
        print(f"Total clean records: {n}")
