"""Tests for the REST API."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def _get_client():
    """Create test client with mocked startup."""
    with patch("src.api.load_static_documents", return_value=[]), \
         patch("src.api.ingest_documents") as mock_ingest, \
         patch("src.api.init_db"), \
         patch("src.api.build_chatbot") as mock_build:

        mock_ingest.return_value = MagicMock()

        mock_chatbot = MagicMock()
        mock_chatbot.invoke.return_value = {
            "response": "Parking costs $5/hour.",
            "guardrail_triggered": False,
        }
        mock_build.return_value = mock_chatbot

        from src.api import app
        return TestClient(app)


def test_health():
    client = _get_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_returns_reply():
    client = _get_client()
    resp = client.post("/chat", json={"session_id": "s1", "message": "prices?"})
    assert resp.status_code == 200
    assert "reply" in resp.json()
    assert len(resp.json()["reply"]) > 0


def test_admin_pending_list():
    with patch("src.api.get_pending_list", return_value=[]):
        client = _get_client()
        resp = client.get("/admin/reservations")
        assert resp.status_code == 200
        assert "reservations" in resp.json()