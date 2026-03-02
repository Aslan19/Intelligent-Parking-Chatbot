"""Main chatbot logic using LangGraph for conversation flow."""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from src.rag_chain import build_rag_chain
from src.guardrails import sanitize_input, sanitize_output
from src.dynamic_db import save_reservation


# ── Conversation State ─────────────────────────────────────────────────
class ChatState(TypedDict, total=False):
    user_message: str
    intent: str                  # "info" or "reservation"
    response: str
    reservation: dict            # collected fields
    guardrail_triggered: bool


# ── Reservation field prompts ──────────────────────────────────────────
RESERVATION_FIELDS = ["first_name", "last_name", "license_plate", "start_time", "end_time"]
FIELD_PROMPTS = {
    "first_name": "Sure, let's make a reservation! What is your **first name**?",
    "last_name": "What is your **last name**?",
    "license_plate": "What is your **vehicle license plate** number?",
    "start_time": "When should the reservation **start**? (e.g. 2025-07-01 09:00)",
    "end_time": "When should it **end**? (e.g. 2025-07-01 18:00)",
}


def build_chatbot(vector_store, db_path=None):
    """Build and return a compiled LangGraph chatbot."""

    rag_ask = build_rag_chain(vector_store, db_path)

    # ── Node: Input guardrail ──────────────────────────────────────
    def input_guard(state: ChatState) -> ChatState:
        cleaned, blocked = sanitize_input(state["user_message"])
        state["user_message"] = cleaned
        if blocked:
            state["guardrail_triggered"] = True
        return state

    # ── Node: Classify intent ──────────────────────────────────────
    def classify(state: ChatState) -> ChatState:
        msg = state["user_message"].lower()
        reservation = state.get("reservation", {})

        # If we're already collecting reservation data, stay in reservation mode
        if reservation and _next_missing_field(reservation):
            state["intent"] = "reservation"
        elif any(w in msg for w in ["reserve", "book", "reservation", "booking"]):
            state["intent"] = "reservation"
        else:
            state["intent"] = "info"
        return state

    # ── Node: RAG info ─────────────────────────────────────────────
    def info_node(state: ChatState) -> ChatState:
        result = rag_ask(state["user_message"])
        state["response"] = result["answer"]
        return state

    # ── Node: Reservation collector ────────────────────────────────
    def reservation_node(state: ChatState) -> ChatState:
        res = state.get("reservation") or {}
        msg = state["user_message"].strip()

        # If starting fresh, don't use the trigger message as a field value
        if not res:
            res = {}
            next_field = _next_missing_field(res)
            state["reservation"] = res
            state["response"] = FIELD_PROMPTS[next_field]
            return state

        # Fill the next missing field with user's message
        next_field = _next_missing_field(res)
        if next_field:
            res[next_field] = msg

        # Check if there are more fields to collect
        next_field = _next_missing_field(res)
        if next_field:
            state["response"] = FIELD_PROMPTS[next_field]
        else:
            # All fields collected — save and summarize
            row_id = save_reservation(res, db_path)
            state["response"] = (
                f"✅ Reservation submitted (#{row_id})!\n\n"
                f"• Name: {res['first_name']} {res['last_name']}\n"
                f"• License plate: {res['license_plate']}\n"
                f"• Period: {res['start_time']} → {res['end_time']}\n\n"
                f"Status: **Pending admin approval**."
            )
            res = {}  # reset for next reservation

        state["reservation"] = res
        return state

    # ── Node: Output guardrail ─────────────────────────────────────
    def output_guard(state: ChatState) -> ChatState:
        cleaned, had_sensitive = sanitize_output(state.get("response", ""))
        state["response"] = cleaned
        if had_sensitive:
            state["guardrail_triggered"] = True
        return state

    # ── Router ─────────────────────────────────────────────────────
    def route(state: ChatState) -> str:
        return state.get("intent", "info")

    # ── Build graph ────────────────────────────────────────────────
    graph = StateGraph(ChatState)

    graph.add_node("input_guard", input_guard)
    graph.add_node("classify", classify)
    graph.add_node("info", info_node)
    graph.add_node("reservation", reservation_node)
    graph.add_node("output_guard", output_guard)

    graph.set_entry_point("input_guard")
    graph.add_edge("input_guard", "classify")
    graph.add_conditional_edges("classify", route, {
        "info": "info",
        "reservation": "reservation"
    })
    graph.add_edge("info", "output_guard")
    graph.add_edge("reservation", "output_guard")
    graph.add_edge("output_guard", END)

    return graph.compile()


def _next_missing_field(reservation: dict) -> Optional[str]:
    """Return the next field that still needs to be collected, or None."""
    for field in RESERVATION_FIELDS:
        if not reservation.get(field):
            return field
    return None