"""REST API: user chat endpoint + admin endpoints for human-in-the-loop."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.loader import load_static_documents
from src.vectorstore import ingest_documents
from src.dynamic_db import init_db
from src.chatbot import build_chatbot
from src.admin_agent import (
    get_pending_list,
    get_reservation_summary,
    approve_reservation,
    reject_reservation,
)

app = FastAPI(title="Parking Chatbot API")

# ── Global state ──────────────────────────────────────────────────────
vector_store = None
chatbot = None
sessions = {}  # session_id → state dict


@app.on_event("startup")
def startup():
    global vector_store, chatbot
    docs = load_static_documents()
    vector_store = ingest_documents(docs)
    init_db()
    chatbot = build_chatbot(vector_store)
    print("✅ API ready")


# ── Request/Response models ───────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str

class ChatResponse(BaseModel):
    reply: str
    reservation_id: Optional[int] = None
    guardrail_triggered: bool = False

class AdminAction(BaseModel):
    comment: str = ""


# ── USER ENDPOINTS ────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """User sends a message, gets a response."""
    session = sessions.get(req.session_id, {})
    session["user_message"] = req.message

    result = chatbot.invoke(session)

    # Preserve state across turns
    sessions[req.session_id] = {
        "reservation": result.get("reservation"),
        "reservation_id": result.get("reservation_id"),
    }

    return ChatResponse(
        reply=result.get("response", "Sorry, something went wrong."),
        reservation_id=result.get("reservation_id"),
        guardrail_triggered=result.get("guardrail_triggered", False),
    )


# ── ADMIN ENDPOINTS ──────────────────────────────────────────────────

@app.get("/admin/reservations")
def list_pending():
    """Admin views all pending reservations."""
    pending = get_pending_list()
    return {"pending_count": len(pending), "reservations": pending}


@app.get("/admin/reservations/{reservation_id}")
def view_reservation(reservation_id: int):
    """Admin views one reservation with LLM-generated summary."""
    res, summary = get_reservation_summary(reservation_id)
    if not res:
        raise HTTPException(404, "Reservation not found")
    return {"reservation": res, "summary": summary}


@app.post("/admin/reservations/{reservation_id}/approve")
def approve(reservation_id: int, action: AdminAction = AdminAction()):
    """Admin approves a reservation."""
    updated = approve_reservation(reservation_id, action.comment)
    if not updated:
        raise HTTPException(404, "Reservation not found")
    return {"message": "Reservation approved", "reservation": updated}


@app.post("/admin/reservations/{reservation_id}/reject")
def reject(reservation_id: int, action: AdminAction = AdminAction()):
    """Admin rejects a reservation."""
    updated = reject_reservation(reservation_id, action.comment)
    if not updated:
        raise HTTPException(404, "Reservation not found")
    return {"message": "Reservation rejected", "reservation": updated}


@app.get("/health")
def health():
    return {"status": "ok"}