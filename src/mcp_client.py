"""MCP Client: calls MCP server to write reservations."""

import logging                                          # ✅ CHANGE #7
import requests
from datetime import datetime
from src.config import MCP_BASE_URL, MCP_API_KEY, MCP_OUTPUT_FILE, MCP_FALLBACK_ENABLED
from src.models import Reservation                      # ✅ CHANGE #6

logger = logging.getLogger(__name__)                    # ✅ CHANGE #7


# ✅ CHANGE #6: accepts Reservation model, not dict
def call_write_reservation(reservation: Reservation) -> dict:
    payload = {
        "reservation_id": reservation.id,
        "first_name": reservation.first_name,
        "last_name": reservation.last_name,
        "license_plate": reservation.license_plate,
        "start_time": reservation.start_time,
        "end_time": reservation.end_time,
    }
    try:
        resp = requests.post(
            f"{MCP_BASE_URL}/tools/write_reservation",
            json=payload,
            headers={"x-api-key": MCP_API_KEY},
            timeout=5
        )
        resp.raise_for_status()
        logger.info("MCP write succeeded for reservation #%s", reservation.id)  # ✅ CHANGE #7
        return resp.json()

    except Exception as e:
        logger.error("MCP server call failed: %s", e)                          # ✅ CHANGE #7

        # ✅ CHANGE #2: Fallback is not silent anymore. Must be explicitly enabled.
        if MCP_FALLBACK_ENABLED:
            logger.warning("MCP_FALLBACK_ENABLED=true — writing locally (BYPASSES AUTH)")
            return local_fallback(reservation)
        else:
            logger.error("MCP_FALLBACK_ENABLED=false — write FAILED. "
                         "Set MCP_FALLBACK_ENABLED=true in .env to allow local writes.")
            return {
                "success": False,
                "message": f"MCP server unavailable and fallback disabled: {e}"
            }


def local_fallback(reservation: Reservation) -> dict:
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{reservation.file_line} | {approval_time}"          # ✅ CHANGE #6: uses model property
    with open(MCP_OUTPUT_FILE, "a") as f:
        f.write(line + "\n")
    logger.warning("Wrote locally (fallback): %s", line)         # ✅ CHANGE #7
    return {"success": True, "message": "Written locally (fallback)", "line": line}