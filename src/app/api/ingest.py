# ruff: noqa: B008

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingestion.service import IngestionError, ingest_files

router = APIRouter(prefix="/ingest", tags=["ingest"])

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"


@router.post("/files")
async def ingest_uploaded_files(
    db: Session = Depends(get_db),
    # NOTE: don't combine Annotated(File(...)) with a default value.
    # On newer FastAPI/Pydantic versions this can short-circuit to 422 before
    # our handler runs, which breaks our contract (we want to return 400 for
    # ingestion schema errors).
    files: list[UploadFile] = File(...),
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        payloads: list[tuple[str, bytes]] = []
        for f in files:
            payloads.append((f.filename or "unknown", await f.read()))

        result = ingest_files(db=db, source="upload", files=payloads)
        return {
            "run_id": str(result.run_id),
            "total_records": result.total_records,
            "inserted_records": result.inserted_records,
            "deduped_records": result.deduped_records,
            "per_file": result.per_file,
        }
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
            "inserted_records": result.inserted_records,
            "deduped_records": result.deduped_records,
            "per_file": result.per_file,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Missing sample file: {e}") from e
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
