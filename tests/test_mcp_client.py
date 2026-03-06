"""Tests for MCP client."""

from src.mcp_client import _local_fallback


def test_local_fallback_writes_file(tmp_path, monkeypatch):
    output_file = str(tmp_path / "fallback.txt")
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)

    result = _local_fallback({
        "first_name": "Jane",
        "last_name": "Smith",
        "license_plate": "XYZ-789",
        "start_time": "2025-08-01 10:00",
        "end_time": "2025-08-01 16:00"
    })

    assert result["success"] is True

    with open(output_file) as f:
        content = f.read()
    assert "Jane Smith" in content
    assert "XYZ-789" in content


def test_local_fallback_appends(tmp_path, monkeypatch):
    output_file = str(tmp_path / "fallback2.txt")
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)

    _local_fallback({"first_name": "A", "last_name": "B", "license_plate": "1",
                     "start_time": "s1", "end_time": "e1"})
    _local_fallback({"first_name": "C", "last_name": "D", "license_plate": "2",
                     "start_time": "s2", "end_time": "e2"})

    with open(output_file) as f:
        lines = f.readlines()
    assert len(lines) == 2