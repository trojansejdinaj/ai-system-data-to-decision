from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_decision_view_page_is_rendered():
    client = TestClient(app)
    r = client.get("/dashboard/decisions")

    assert r.status_code == 200
    assert "Decision View" in r.text
    assert "/decisions/latest" in r.text
    assert "/decisions?limit=" in r.text
