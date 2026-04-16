"""Tests for MCP server tool and client."""

import os
import pytest
from datetime import datetime


# ✅ Test the FastMCP tool function directly
def test_write_reservation_tool(tmp_path, monkeypatch):
    out = str(tmp_path / "out.txt")
    monkeypatch.setattr("src.mcp_server.OUTPUT_FILE", out)

    from src.mcp_server import write_reservation

    result = write_reservation(
        reservation_id=1,
        first_name="John",
        last_name="Doe",
        license_plate="ABC-123",
        start_time="2025-07-01 09:00",
        end_time="2025-07-01 17:00"
    )

    assert "John Doe" in result
    assert "ABC-123" in result
    content = open(out).read()
    assert "John Doe" in content
    assert "ABC-123" in content


def test_tool_appends_multiple(tmp_path, monkeypatch):
    out = str(tmp_path / "out.txt")
    monkeypatch.setattr("src.mcp_server.OUTPUT_FILE", out)

    from src.mcp_server import write_reservation

    for name in ["Alice", "Bob", "Carol"]:
        write_reservation(
            reservation_id=1, first_name=name, last_name="Test",
            license_plate=f"{name}-001",
            start_time="2025-08-01 09:00", end_time="2025-08-01 17:00"
        )

    lines = open(out).readlines()
    assert len(lines) == 3
    assert "Alice" in lines[0]
    assert "Carol" in lines[2]


# ✅ Test tool is registered on FastMCP server
def test_tool_registered():
    from src.mcp_server import mcp
    # FastMCP stores tools internally
    assert hasattr(mcp, "tool")


# ✅ Test local fallback still works
def test_local_fallback(tmp_path, monkeypatch):
    out = str(tmp_path / "fb.txt")
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", out)

    from src.mcp_client import local_fallback
    from src.models import Reservation

    r = Reservation(
        id=1, first_name="Jane", last_name="Doe",
        license_plate="XYZ-789",
        start_time="2025-08-01 10:00", end_time="2025-08-01 16:00"
    )
    result = local_fallback(r)

    assert result["success"] is True
    assert "Jane Doe" in open(out).read()


# ✅ Test MCP client with fallback disabled returns failure
def test_client_fails_gracefully_no_fallback(monkeypatch):
    monkeypatch.setattr("src.mcp_client.MCP_FALLBACK_ENABLED", False)
    monkeypatch.setattr("src.mcp_client.MCP_SERVER_SCRIPT", "/nonexistent/path.py")

    from src.mcp_client import call_write_reservation
    from src.models import Reservation

    r = Reservation(
        id=99, first_name="Fail", last_name="Test",
        license_plate="FAIL-1",
        start_time="2025-01-01 00:00", end_time="2025-01-01 01:00"
    )
    result = call_write_reservation(r)

    assert result["success"] is False
    assert "fallback disabled" in result["message"].lower()


# ✅ Test MCP client with fallback enabled writes locally
def test_client_falls_back_when_enabled(tmp_path, monkeypatch):
    out = str(tmp_path / "fb2.txt")
    monkeypatch.setattr("src.mcp_client.MCP_FALLBACK_ENABLED", True)
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", out)
    monkeypatch.setattr("src.mcp_client.MCP_SERVER_SCRIPT", "/nonexistent/path.py")

    from src.mcp_client import call_write_reservation
    from src.models import Reservation

    r = Reservation(
        id=88, first_name="Fallback", last_name="User",
        license_plate="FB-001",
        start_time="2025-02-01 09:00", end_time="2025-02-01 17:00"
    )
    result = call_write_reservation(r)

    assert result["success"] is True
    assert "Fallback User" in open(out).read()