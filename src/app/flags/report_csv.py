from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from .models import FlaggedRecord

REPORT_COLUMNS = [
    "id",
    "run_id",
    "row_num",
    "source",
    "source_id",
    "category",
    "event_time",
    "value",
    "record_hash",
    "ingested_at",
    "severity",
    "flag_codes",
    "flag_messages",
]


def write_flag_report_csv(flagged: Iterable[FlaggedRecord], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        w.writeheader()
        for fr in flagged:
            r = fr.record
            w.writerow(
                {
                    "id": r.get("id", ""),
                    "run_id": r.get("run_id", ""),
                    "row_num": r.get("row_num", ""),
                    "source": r.get("source", ""),
                    "source_id": r.get("source_id", ""),
                    "category": r.get("category", ""),
                    "event_time": r.get("event_time", ""),
                    "value": r.get("value", ""),
                    "record_hash": r.get("record_hash", ""),
                    "ingested_at": r.get("ingested_at", ""),
                    "severity": fr.severity,
                    "flag_codes": fr.flag_codes,
                    "flag_messages": fr.flag_messages,
                }
            )

    return out_path
