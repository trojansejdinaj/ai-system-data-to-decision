import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import SessionLocal
from app.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def _truncate_ingestion_tables() -> None:
    """Keep integration tests deterministic by clearing ingestion tables."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE TABLE raw_records, ingest_runs CASCADE;"))
        db.commit()


def _count(table_name: str) -> int:
    with SessionLocal() as db:
        return int(db.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar_one())


def test_ingest_samples_works():
    _truncate_ingestion_tables()

    r = client.post("/ingest/samples")
    assert r.status_code == 200, r.text
    data = r.json()

    assert "run_id" in data
    assert data["total_records"] > 0
    assert data["inserted_records"] > 0
    assert "sample.csv" in data["per_file"]
    assert "sample.xlsx" in data["per_file"]


def test_ingest_samples_is_idempotent():
    _truncate_ingestion_tables()

    r1 = client.post("/ingest/samples")
    assert r1.status_code == 200, r1.text

    c1 = _count("raw_records")
    assert c1 > 0

    r2 = client.post("/ingest/samples")
    assert r2.status_code == 200, r2.text

    c2 = _count("raw_records")
    assert c2 == c1, "raw_records should not grow on repeated ingestion"

    runs = _count("ingest_runs")
    assert runs == 2, "we expect to track both ingestion runs"


def test_ingest_csv_missing_column_fails():
    _truncate_ingestion_tables()

    bad = "source_id,event_time,value\nx,2026-01-01T00:00:00Z,1\n"
    files = [("files", ("bad.csv", bad.encode("utf-8"), "text/csv"))]

    r = client.post("/ingest/files", files=files)
    assert r.status_code == 400
    assert "Missing required columns" in r.text
