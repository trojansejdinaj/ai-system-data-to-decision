from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingestion.service import IngestionError, ingest_files

router = APIRouter(prefix="/ingest", tags=["ingest"])

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"


@router.post("/files")
async def ingest_uploaded_files(
    db: Session = Depends(get_db),
    files: Annotated[list[UploadFile], File(...)] = [],
):
    try:
        payloads: list[tuple[str, bytes]] = []
        for f in files:
            payloads.append((f.filename or "unknown", await f.read()))

        result = ingest_files(db=db, source="upload", files=payloads)
        return {
            "run_id": str(result.run_id),
            "total_records": result.total_records,
            "per_file": result.per_file,
        }
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/samples")
def ingest_samples(db: Session = Depends(get_db)):
    try:
        files = [
            ("sample.csv", (SAMPLES_DIR / "sample.csv").read_bytes()),
            ("sample.xlsx", (SAMPLES_DIR / "sample.xlsx").read_bytes()),
        ]
        result = ingest_files(db=db, source="samples", files=files)
        return {
            "run_id": str(result.run_id),
            "total_records": result.total_records,
            "per_file": result.per_file,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Missing sample file: {e}")
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))
