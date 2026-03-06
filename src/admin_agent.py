"""Admin agent: reviews reservations, writes to file via MCP on approval."""

from src.dynamic_db import (
    get_pending_reservations,
    get_reservation,
    update_reservation_status,
)
from src.mcp_client import call_write_reservation


def get_pending_list(db_path=None):
    return get_pending_reservations(db_path)


def approve_reservation(reservation_id: int, comment: str = "", db_path=None):
    """Approve reservation → update DB → write to file via MCP server."""
    updated = update_reservation_status(reservation_id, "approved", comment, db_path)
    if not updated:
        return None

    # Call MCP server to write confirmed reservation to file
    result = call_write_reservation(updated)
    print(f"  📝 {result.get('message', 'Written to file')}")

    return updated


def reject_reservation(reservation_id: int, comment: str = "", db_path=None):
    return update_reservation_status(reservation_id, "rejected", comment, db_path)


def notify_admin(reservation: dict):
    print(f"\n🔔 NEW RESERVATION REQUEST #{reservation['id']}")
    print(f"   {reservation['first_name']} {reservation['last_name']}")
    print(f"   Plate: {reservation['license_plate']}")
    print(f"   Period: {reservation['start_time']} → {reservation['end_time']}")
    return reservation