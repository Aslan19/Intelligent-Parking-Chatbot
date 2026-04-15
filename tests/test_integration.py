"""Integration tests using Pydantic models."""

from src.dynamic_db import save_reservation, get_reservation, update_reservation_status
from src.mcp_client import local_fallback
from src.models import Reservation, ReservationCreate            # ✅ CHANGE #6


# ✅ CHANGE #6: uses ReservationCreate model
SAMPLE = ReservationCreate(
    first_name="John", last_name="Doe", license_plate="ABC-123",
    start_time="2025-07-01 09:00", end_time="2025-07-01 17:00"
)


def test_full_flow(db, output_file, monkeypatch):
    monkeypatch.setattr("src.mcp_client.MCP_FALLBACK_ENABLED", True)
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)

    saved = save_reservation(SAMPLE, db)                         # ✅ CHANGE #6: returns Reservation
    assert isinstance(saved, Reservation)
    assert saved.status == "pending_approval"

    updated = update_reservation_status(saved.id, "approved", "OK", db)
    assert updated.status == "approved"                          # ✅ CHANGE #6: dot access

    result = local_fallback(updated)                             # ✅ CHANGE #6: passes model
    assert result["success"] is True
    content = open(output_file).read()
    assert "John Doe" in content
    assert "ABC-123" in content


def test_rejected_not_written(db, output_file):
    saved = save_reservation(SAMPLE, db)
    update_reservation_status(saved.id, "rejected", "Full", db)
    r = get_reservation(saved.id, db)
    assert r.status == "rejected"                                # ✅ CHANGE #6
    import os
    assert not os.path.exists(output_file)


def test_multiple_approvals(db, output_file, monkeypatch):
    monkeypatch.setattr("src.mcp_client.MCP_FALLBACK_ENABLED", True)
    monkeypatch.setattr("src.mcp_client.MCP_OUTPUT_FILE", output_file)
    for name in ["Alice", "Bob", "Carol"]:
        data = ReservationCreate(                                # ✅ CHANGE #6
            first_name=name, last_name="Test", license_plate=f"{name}-001",
            start_time="2025-09-01 09:00", end_time="2025-09-01 17:00"
        )
        saved = save_reservation(data, db)
        updated = update_reservation_status(saved.id, "approved", "", db)
        local_fallback(updated)
    assert len(open(output_file).readlines()) == 3