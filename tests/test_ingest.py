import pytest
pytestmark = pytest.mark.integration

import pytest

pytestmark = pytest.mark.integration


from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ingest_samples_works():
    r = client.post("/ingest/samples")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "run_id" in data
    assert data["total_records"] > 0
    assert "sample.csv" in data["per_file"]
    assert "sample.xlsx" in data["per_file"]


def test_ingest_csv_missing_column_fails():
    bad = "source_id,event_time,value\nx,2026-01-01T00:00:00Z,1\n"
    files = [("files", ("bad.csv", bad.encode("utf-8"), "text/csv"))]
    r = client.post("/ingest/files", files=files)
    assert r.status_code == 400
    assert "Missing required columns" in r.text
