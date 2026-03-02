"""Admin agent: reviews reservations, generates summaries, notifies admin."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import OPENAI_API_KEY, MODEL_NAME
from src.dynamic_db import (
    get_pending_reservations,
    get_reservation,
    update_reservation_status,
)

# LLM used by admin agent to summarize reservations
llm = ChatOpenAI(model=MODEL_NAME, temperature=0, openai_api_key=OPENAI_API_KEY)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a parking admin assistant. Summarize this reservation "
               "clearly for the administrator to review."),
    ("human", "Reservation #{id}:\n"
              "Name: {first_name} {last_name}\n"
              "License plate: {license_plate}\n"
              "Period: {start_time} → {end_time}\n"
              "Status: {status}")
])

summary_chain = SUMMARY_PROMPT | llm | StrOutputParser()


def get_pending_list(db_path=None):
    """Get all pending reservations as a list of dicts."""
    return get_pending_reservations(db_path)


def get_reservation_summary(reservation_id: int, db_path=None):
    """Use LLM to generate a human-readable summary for admin."""
    res = get_reservation(reservation_id, db_path)
    if not res:
        return None, "Reservation not found."

    summary = summary_chain.invoke({
        "id": res["id"],
        "first_name": res["first_name"],
        "last_name": res["last_name"],
        "license_plate": res["license_plate"],
        "start_time": res["start_time"],
        "end_time": res["end_time"],
        "status": res["status"],
    })
    return res, summary


def approve_reservation(reservation_id: int, comment: str = "", db_path=None):
    """Admin approves a reservation."""
    updated = update_reservation_status(reservation_id, "approved", comment, db_path)
    if not updated:
        return None
    return updated


def reject_reservation(reservation_id: int, comment: str = "", db_path=None):
    """Admin rejects a reservation."""
    updated = update_reservation_status(reservation_id, "rejected", comment, db_path)
    if not updated:
        return None
    return updated


def notify_admin(reservation: dict):
    """
    Send notification to admin about a new reservation.
    In production: send email / Slack / Teams message.
    Here: prints to console + returns notification text.
    """
    text = (
        f"🔔 NEW RESERVATION REQUEST #{reservation['id']}\n"
        f"   Name: {reservation['first_name']} {reservation['last_name']}\n"
        f"   Plate: {reservation['license_plate']}\n"
        f"   Period: {reservation['start_time']} → {reservation['end_time']}\n"
        f"   → Review at: POST /admin/reservations/{reservation['id']}/approve\n"
        f"   → Or reject:  POST /admin/reservations/{reservation['id']}/reject"
    )
    print(text)
    return text