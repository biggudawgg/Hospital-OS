"""
tests/test_api.py — Tests for the FastAPI backend (runs without MCP servers or an LLM).
"""

import pytest
from fastapi.testclient import TestClient

from backend import dashboard_routes
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("path", ["/", "/patients", "/doctors", "/appointments", "/wards",
                                  "/beds", "/medicines", "/lab_tests", "/bills"])
def test_list_endpoints(client, path):
    assert client.get(path).status_code == 200


def test_seed_counts(client):
    assert len(client.get("/patients").json()) == 100
    assert len(client.get("/doctors").json()) == 15
    assert len(client.get("/wards").json()) == 5
    assert len(client.get("/beds").json()) == 60
    assert len(client.get("/medicines").json()) == 50


def test_missing_item_is_404(client):
    assert client.get("/patients/9999").status_code == 404


def test_stats_are_consistent(client):
    s = client.get("/stats").json()
    assert s["beds_total"] == s["beds_occupied"] + s["beds_free"] == 60
    assert s["beds_occupied"] == s["patients_admitted"]          # beds and patients stay in sync
    assert len(s["appointments_next_7_days"]) == 7


def test_generic_put_cannot_desync_beds(client):
    r = client.put("/beds/1", json={"is_occupied": False})
    assert r.status_code == 400
    r = client.put("/patients/1", json={"is_admitted": False})
    assert r.status_code == 400


def test_admit_and_discharge_routes(client):
    r = client.post("/beds/admit", json={"patient_id": 3, "ward": "ICU"})
    assert r.status_code == 200, r.text
    assert client.get("/patients/3").json()["is_admitted"] is True
    assert client.post("/beds/discharge", json={"patient_id": 3}).status_code == 200


def test_chat_without_agent_is_friendly(client):
    r = client.post("/chat", json={"message": "hi", "history": []})
    assert r.status_code == 200 and r.json()["error"] is True


def test_chat_rejects_empty_message(client):
    assert client.post("/chat", json={"message": "", "history": []}).status_code == 422


def test_reports_generate_list_read(client, tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_routes, "REPORTS_DIR", tmp_path)
    name = client.post("/reports/occupancy").json()["name"]
    assert any(r["name"] == name for r in client.get("/reports").json())
    assert "Bed Occupancy Report" in client.get(f"/reports/{name}").json()["content"]
    assert client.get("/reports/..%2F.env").status_code == 404     # cannot escape reports/
