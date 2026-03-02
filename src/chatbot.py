"""Main chatbot logic using LangGraph for conversation flow."""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from src.rag_chain import build_rag_chain
from src.guardrails import sanitize_input, sanitize_output
from src.dynamic_db import save_reservation, get_reservation
from src.admin_agent import notify_admin


class ChatState(TypedDict, total=False):
    user_message: str
    intent: str
    response: str
    reservation: Optional[dict]
    reservation_id: Optional[int]
    guardrail_triggered: bool


RESERVATION_FIELDS = ["first_name", "last_name", "license_plate", "start_time", "end_time"]
FIELD_PROMPTS = {
    "first_name": "Sure, let's make a reservation! What is your **first name**?",
    "last_name": "What is your **last name**?",
    "license_plate": "What is your **vehicle license plate** number?",
    "start_time": "When should the reservation **start**? (e.g. 2025-07-01 09:00)",
    "end_time": "When should it **end**? (e.g. 2025-07-01 18:00)",
}


def _next_missing_field(reservation: dict) -> Optional[str]:
    for field in RESERVATION_FIELDS:
        if not reservation.get(field):
            return field
    return None


def build_chatbot(vector_store, db_path=None):
    rag_ask = build_rag_chain(vector_store, db_path)

    def input_guard(state: ChatState) -> ChatState:
        cleaned, blocked = sanitize_input(state["user_message"])
        state["user_message"] = cleaned
        if blocked:
            state["guardrail_triggered"] = True
        return state

    def classify(state: ChatState) -> ChatState:
        msg = state["user_message"].lower()
        reservation = state.get("reservation")

        # Already collecting → stay in reservation mode
        if reservation is not None and _next_missing_field(reservation):
            state["intent"] = "reservation"
        # Check reservation status
        elif any(w in msg for w in ["status", "check reservation", "my reservation"]):
            state["intent"] = "check_status"
        elif any(w in msg for w in ["reserve", "book", "reservation", "booking"]):
            state["intent"] = "reservation"
        else:
            state["intent"] = "info"
        return state

    def info_node(state: ChatState) -> ChatState:
        result = rag_ask(state["user_message"])
        state["response"] = result["answer"]
        return state

    def reservation_node(state: ChatState) -> ChatState:
        reservation = state.get("reservation")
        msg = state["user_message"].strip()

        # First time → ask first question
        if reservation is None:
            state["reservation"] = {}
            state["response"] = FIELD_PROMPTS["first_name"]
            return state

        # Fill next missing field
        next_field = _next_missing_field(reservation)
        if next_field:
            reservation[next_field] = msg

        # Check if more fields needed
        next_field = _next_missing_field(reservation)
        if next_field:
            state["response"] = FIELD_PROMPTS[next_field]
        else:
            # All done → save to DB
            row_id = save_reservation(reservation, db_path)

            # Get full record and notify admin
            saved = get_reservation(row_id, db_path)
            notify_admin(saved)

            state["response"] = (
                f"✅ Reservation submitted (#{row_id})!\n\n"
                f"• Name: {reservation['first_name']} {reservation['last_name']}\n"
                f"• License plate: {reservation['license_plate']}\n"
                f"• Period: {reservation['start_time']} → {reservation['end_time']}\n\n"
                f"📨 An administrator has been notified and will review your request.\n"
                f"You can check status anytime by asking: **check my reservation**"
            )
            state["reservation_id"] = row_id
            state["reservation"] = None  # reset

        return state

    def check_status_node(state: ChatState) -> ChatState:
        rid = state.get("reservation_id")
        if not rid:
            state["response"] = "I don't have a reservation on file for you. Would you like to make one?"
            return state

        res = get_reservation(rid, db_path)
        if not res:
            state["response"] = "Reservation not found."
            return state

        status = res["status"]
        comment = res.get("admin_comment", "")

        if status == "approved":
            state["response"] = f"✅ Reservation #{rid} has been **approved**!"
            if comment:
                state["response"] += f"\nAdmin note: {comment}"
        elif status == "rejected":
            state["response"] = f"❌ Reservation #{rid} has been **rejected**."
            if comment:
                state["response"] += f"\nReason: {comment}"
        else:
            state["response"] = f"⏳ Reservation #{rid} is still **pending approval**."

        return state

    def output_guard(state: ChatState) -> ChatState:
        cleaned, had_sensitive = sanitize_output(state.get("response", ""))
        state["response"] = cleaned
        if had_sensitive:
            state["guardrail_triggered"] = True
        return state

    def route(state: ChatState) -> str:
        return state.get("intent", "info")

    # Build graph
    graph = StateGraph(ChatState)

    graph.add_node("input_guard", input_guard)
    graph.add_node("classify", classify)
    graph.add_node("info", info_node)
    graph.add_node("reservation", reservation_node)
    graph.add_node("check_status", check_status_node)
    graph.add_node("output_guard", output_guard)

    graph.set_entry_point("input_guard")
    graph.add_edge("input_guard", "classify")
    graph.add_conditional_edges("classify", route, {
        "info": "info",
        "reservation": "reservation",
        "check_status": "check_status",
    })
    graph.add_edge("info", "output_guard")
    graph.add_edge("reservation", "output_guard")
    graph.add_edge("check_status", "output_guard")
    graph.add_edge("output_guard", END)

    return graph.compile()