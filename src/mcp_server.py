"""MCP Server: writes confirmed reservations to file. Runs on port 8001."""

from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from src.config import MCP_API_KEY, MCP_OUTPUT_FILE

app = FastAPI(title="Parking MCP Server")


def verify_key(x_api_key: str = Header(...)):
    if x_api_key != MCP_API_KEY:
        raise HTTPException(401, "Invalid API key")


class ReservationRecord(BaseModel):
    reservation_id: int
    first_name: str
    last_name: str
    license_plate: str
    start_time: str
    end_time: str


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
        raise HTTPException(500, f"File write failed: {e}")
    return {"success": True, "message": f"Reservation #{record.reservation_id} written.", "line": line}


@app.get("/tools/list")
def list_tools(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    return {"tools": [{"name": "write_reservation", "endpoint": "/tools/write_reservation", "method": "POST"}]}


@app.get("/health")
def health():
    return {"status": "ok"}