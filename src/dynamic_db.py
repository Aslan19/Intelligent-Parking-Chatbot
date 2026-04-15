"""SQLite database for dynamic data and reservations."""

import json
import logging                                          # ✅ CHANGE #7
import sqlite3
from typing import Optional, List
from src.config import SQLITE_PATH, DATA_PATH
from src.models import Reservation, ReservationCreate   # ✅ CHANGE #6

logger = logging.getLogger(__name__)                    # ✅ CHANGE #7


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None, data_path=None):
    conn = get_connection(db_path)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS working_hours
                 (day_type TEXT PRIMARY KEY, hours TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS pricing
                 (item TEXT PRIMARY KEY, value REAL, currency TEXT DEFAULT 'USD')""")
    c.execute("""CREATE TABLE IF NOT EXISTS availability
                 (level TEXT PRIMARY KEY, available INTEGER, total INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reservations (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 first_name TEXT, last_name TEXT, license_plate TEXT,
                 start_time TEXT, end_time TEXT,
                 status TEXT DEFAULT 'pending_approval',
                 admin_comment TEXT DEFAULT '',
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    if c.execute("SELECT COUNT(*) FROM working_hours").fetchone()[0] == 0:
        raw = json.loads(open(data_path or DATA_PATH).read())
        dyn = raw["dynamic"]
        for day_type, hours in dyn["working_hours"].items():
            c.execute("INSERT INTO working_hours VALUES (?,?)", (day_type, hours))
        currency = dyn["pricing"].get("currency", "USD")
        for item, val in dyn["pricing"].items():
            if item != "currency":
                c.execute("INSERT INTO pricing VALUES (?,?,?)", (item, val, currency))
        for row in dyn["availability"]:
            c.execute("INSERT INTO availability VALUES (?,?,?)",
                      (row["level"], row["available"], row["total"]))
        logger.info("Database seeded from %s", data_path or DATA_PATH)  # ✅ CHANGE #7

    conn.commit()
    conn.close()


def get_dynamic_context(db_path=None) -> str:
    conn = get_connection(db_path)
    c = conn.cursor()
    lines = ["LIVE PARKING DATA:"]

    lines.append("\nWorking Hours:")
    for r in c.execute("SELECT * FROM working_hours"):
        lines.append(f"  {r['day_type']}: {r['hours']}")

    lines.append("\nPricing:")
    for r in c.execute("SELECT * FROM pricing"):
        lines.append(f"  {r['item']}: ${r['value']} {r['currency']}")

    lines.append("\nSpace Availability:")
    for r in c.execute("SELECT * FROM availability"):
        lines.append(f"  Level {r['level']}: {r['available']}/{r['total']} spaces free")

    conn.close()
    return "\n".join(lines)


# ✅ CHANGE #6: accepts Pydantic model, returns Reservation
def save_reservation(data: ReservationCreate, db_path=None) -> Reservation:
    conn = get_connection(db_path)
    c = conn.execute(
        "INSERT INTO reservations (first_name,last_name,license_plate,start_time,end_time) "
        "VALUES (?,?,?,?,?)",
        (data.first_name, data.last_name, data.license_plate,
         data.start_time, data.end_time))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    logger.info("Reservation #%d saved", rid)                    # ✅ CHANGE #7
    return get_reservation(rid, db_path)


# ✅ CHANGE #6: returns Reservation model or None
def get_reservation(reservation_id: int, db_path=None) -> Optional[Reservation]:
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return Reservation(**dict(row))                              # ✅ CHANGE #6: dict → model


# ✅ CHANGE #6: returns list of Reservation models
def get_pending_reservations(db_path=None) -> List[Reservation]:
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM reservations WHERE status='pending_approval' ORDER BY id"
    ).fetchall()
    conn.close()
    return [Reservation(**dict(r)) for r in rows]                # ✅ CHANGE #6


# ✅ CHANGE #6: returns Reservation model
def update_reservation_status(reservation_id: int, status: str,
                              comment: str = "", db_path=None) -> Optional[Reservation]:
    if status not in ("approved", "rejected"):
        logger.warning("Invalid status '%s' for #%d", status, reservation_id)  # ✅ CHANGE #7
        return None
    conn = get_connection(db_path)
    conn.execute("UPDATE reservations SET status=?, admin_comment=? WHERE id=?",
                 (status, comment, reservation_id))
    conn.commit()
    conn.close()
    logger.info("Reservation #%d → %s", reservation_id, status)               # ✅ CHANGE #7
    return get_reservation(reservation_id, db_path)