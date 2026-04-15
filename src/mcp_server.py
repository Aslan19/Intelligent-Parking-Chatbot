"""MCP Server: writes confirmed reservations to file."""

import logging                                                   # ✅ CHANGE #7
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from src.config import MCP_API_KEY, MCP_OUTPUT_FILE
from src.models import ReservationRecord                         # ✅ CHANGE #6: shared model

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7

app = FastAPI(title="Parking MCP Server")


def verify_key(x_api_key: str = Header(...)):
    if x_api_key != MCP_API_KEY:
        logger.warning("UNAUTHORIZED request with key: %s***", x_api_key[:4])  # ✅ CHANGE #7
        raise HTTPException(401, "Invalid API key")


@app.post("/tools/write_reservation")
def write_reservation(record: ReservationRecord, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"{record.first_name} {record.last_name} | "
            f"{record.license_plate} | "
            f"{record.start_time} - {record.end_time} | "
            f"{approval_time}")
    try:
        with open(MCP_OUTPUT_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.error("File write failed: %s", e)                               # ✅ CHANGE #7
        raise HTTPException(500, f"File write failed: {e}")
    logger.info("Written: %s", line)                                            # ✅ CHANGE #7
    return {"success": True, "message": f"Reservation #{record.reservation_id} written.", "line": line}


@app.get("/tools/list")
def list_tools(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    return {"tools": [{"name": "write_reservation", "endpoint": "/tools/write_reservation", "method": "POST"}]}


@app.get("/health")
def health():
    return {"status": "ok"}