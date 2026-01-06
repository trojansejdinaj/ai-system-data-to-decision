from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.db.models import IngestRun, RawRecord

REQUIRED_COLUMNS = ["source_id", "event_time", "value", "category"]


class IngestionError(ValueError):
    pass


@dataclass(frozen=True)
class IngestResult:
    run_id: uuid.UUID
    total_records: int
    per_file: dict[str, int]


def _validate_headers(headers: list[str]) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise IngestionError(f"Missing required columns: {missing}")


def _parse_csv(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    _validate_headers(headers)
    return [row for row in reader]


def _parse_xlsx(data: bytes) -> list[dict]:
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip() for h in rows[0]]
    _validate_headers(headers)
    out: list[dict] = []
    for r in rows[1:]:
        row = {headers[i]: r[i] for i in range(len(headers))}
        out.append(row)
    return out


def _parse_by_extension(filename: str, data: bytes) -> list[dict]:
    name = filename.lower()
    if name.endswith(".csv"):
        return _parse_csv(data)
    if name.endswith(".xlsx"):
        return _parse_xlsx(data)
    raise IngestionError(f"Unsupported file type: {filename}")


def ingest_files(db: Session, source: str, files: list[tuple[str, bytes]]) -> IngestResult:
    run = IngestRun(source=source, files="\n".join([f[0] for f in files]), status="started")
    db.add(run)
    db.flush()  # get run.id

    per_file: dict[str, int] = {}
    total = 0

    try:
        for filename, data in files:
            rows = _parse_by_extension(filename, data)
            per_file[filename] = len(rows)
            total += len(rows)

            for idx, payload in enumerate(rows, start=1):
                db.add(
                    RawRecord(
                        run_id=run.id,
                        row_num=idx,
                        payload=payload,
                    )
                )

        run.status = "success"
        db.commit()
        return IngestResult(run_id=run.id, total_records=total, per_file=per_file)

    except Exception as e:
        db.rollback()
        run.status = "failed"
        run.error = str(e)
        db.add(run)
        db.commit()
        raise
