from fastapi.testclient import TestClient
from src.mcp_server import app
from src.config import MCP_API_KEY
from src.mcp_client import local_fallback

client = TestClient(app)
HEADERS = {"x-api-key": MCP_API_KEY}


def test_health():
    assert client.get("/health").status_code == 200


def test_list_tools():
    resp = client.get("/tools/list", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["tools"]) == 1


def test_write_reservation(tmp_path, monkeypatch):
    out = str(tmp_path / "out.txt")
    monkeypatch.setattr("src.mcp_server.MCP_OUTPUT_FILE", out)
    resp = client.post("/tools/write_reservation", headers=HEADERS, json={
        "reservation_id": 1, "first_name": "John", "last_name": "Doe",
        "license_plate": "ABC-123", "start_time": "2025-07-01 09:00",
        "end_time": "2025-07-01 17:00"
    })
    assert resp.json()["success"] is True
    assert "John Doe" in open(out).read()


def test_unauthorized():
    resp = client.post("/tools/write_reservation", headers={"x-api-key": "wrong"},
        json={"reservation_id": 1, "first_name": "X", "last_name": "Y",
              "license_plate": "Z", "start_time": "a", "end_time": "b"})
    assert resp.status_code == 401


def test_local_fallback(tmp_path, monkeypatch):
    out = str(tmp_path / "fb.txt")
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", out)
    result = local_fallback({"first_name": "Jane", "last_name": "Doe",
        "license_plate": "XYZ-789", "start_time": "2025-08-01 10:00",
        "end_time": "2025-08-01 16:00"})
    assert result["success"] is True
    assert "Jane Doe" in open(out).read()