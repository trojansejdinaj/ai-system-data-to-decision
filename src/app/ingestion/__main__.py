from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.ingestion.service import ingest_files


def _samples_dir() -> Path:
    # repo_root/data/samples
    return Path(__file__).resolve().parents[3] / "data" / "samples"


def main() -> int:
    p = argparse.ArgumentParser(description="Run ingestion from CLI (used by make demo).")
    p.add_argument(
        "--samples",
        action="store_true",
        help="Ingest repo sample files (data/samples/sample.csv + sample.xlsx).",
    )
    p.add_argument(
        "--source",
        default="samples",
        help="Source label stored on ingest_runs/raw_records (default: samples).",
    )
    args = p.parse_args()

    if not args.samples:
        print("Nothing to do. Try: python -m app.ingestion --samples", file=sys.stderr)
        return 2

    samples = _samples_dir()
    files = [
        ("sample.csv", (samples / "sample.csv").read_bytes()),
        ("sample.xlsx", (samples / "sample.xlsx").read_bytes()),
    ]

    db = SessionLocal()
    try:
        result = ingest_files(db=db, source=args.source, files=files)
        print(
            json.dumps(
                {
                    "pipeline": "ingest",
                    "run_id": str(result.run_id),
                    "status": "succeeded",
                    "total_records": result.total_records,
                    "inserted_records": result.inserted_records,
                    "deduped_records": result.deduped_records,
                    "per_file": result.per_file,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
