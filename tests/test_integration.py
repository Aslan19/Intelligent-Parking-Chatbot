from src.dynamic_db import save_reservation, get_reservation, update_reservation_status
from src.mcp_client import local_fallback
from tests.conftest import SAMPLE_RESERVATION


def test_full_flow_book_approve_write(db, output_file, monkeypatch):
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)

    # User books
    rid = save_reservation(SAMPLE_RESERVATION, db)
    assert get_reservation(rid, db)["status"] == "pending_approval"

    # Admin approves
    updated = update_reservation_status(rid, "approved", "OK", db)
    assert updated["status"] == "approved"

    # MCP writes
    result = local_fallback(updated)
    assert result["success"] is True
    content = open(output_file).read()
    assert "John Doe" in content
    assert "ABC-123" in content


def test_rejected_not_written(db, output_file):
    rid = save_reservation(SAMPLE_RESERVATION, db)
    update_reservation_status(rid, "rejected", "Full", db)
    r = get_reservation(rid, db)
    assert r["status"] == "rejected"
    import os
    assert not os.path.exists(output_file)


def test_multiple_approvals(db, output_file, monkeypatch):
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)
    for name in ["Alice", "Bob", "Carol"]:
        data = {**SAMPLE_RESERVATION, "first_name": name}
        rid = save_reservation(data, db)
        updated = update_reservation_status(rid, "approved", "", db)
        local_fallback(updated)
    assert len(open(output_file).readlines()) == 3