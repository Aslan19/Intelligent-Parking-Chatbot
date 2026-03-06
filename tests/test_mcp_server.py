"""Tests for MCP server."""

from fastapi.testclient import TestClient
from src.mcp_server import app
from src.config import MCP_API_KEY


client = TestClient(app)
HEADERS = {"x-api-key": MCP_API_KEY}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "mcp-server"


def test_list_tools():
    resp = client.get("/tools/list", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["tools"]) == 1
    assert resp.json()["tools"][0]["name"] == "write_reservation"


def test_write_reservation(tmp_path, monkeypatch):
    output_file = str(tmp_path / "test_output.txt")
    monkeypatch.setattr("src.mcp_server.MCP_OUTPUT_FILE", output_file)

    resp = client.post("/tools/write_reservation", headers=HEADERS, json={
        "reservation_id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "license_plate": "ABC-123",
        "start_time": "2025-07-01 09:00",
        "end_time": "2025-07-01 17:00"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    with open(output_file) as f:
        content = f.read()
    assert "John Doe" in content
    assert "ABC-123" in content


def test_unauthorized_rejected():
    resp = client.post("/tools/write_reservation",
        headers={"x-api-key": "wrong-key"},
        json={
            "reservation_id": 1, "first_name": "X", "last_name": "Y",
            "license_plate": "Z", "start_time": "a", "end_time": "b"
        })
    assert resp.status_code == 401