"""MCP Client: calls MCP server to write reservations. Falls back to local write."""

import requests
from datetime import datetime
from src.config import MCP_BASE_URL, MCP_API_KEY, MCP_OUTPUT_FILE


def call_write_reservation(reservation: dict) -> dict:
    payload = {
        "reservation_id": reservation["id"],
        "first_name": reservation["first_name"],
        "last_name": reservation["last_name"],
        "license_plate": reservation["license_plate"],
        "start_time": reservation["start_time"],
        "end_time": reservation["end_time"],
    }
    try:
        resp = requests.post(
            f"{MCP_BASE_URL}/tools/write_reservation",
            json=payload,
            headers={"x-api-key": MCP_API_KEY},
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️  MCP unavailable ({e}). Writing locally.")
        return local_fallback(reservation)


def local_fallback(reservation: dict) -> dict:
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"{reservation['first_name']} {reservation['last_name']} | "
            f"{reservation['license_plate']} | "
            f"{reservation['start_time']} - {reservation['end_time']} | "
            f"{approval_time}")
    with open(MCP_OUTPUT_FILE, "a") as f:
        f.write(line + "\n")
    return {"success": True, "message": "Written locally (fallback)", "line": line}