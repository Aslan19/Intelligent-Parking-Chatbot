"""Unified LangGraph pipeline: user chat + admin approval + MCP file write."""

import logging                                                   # ✅ CHANGE #7
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from langchain_openai import ChatOpenAI                          # ✅ CHANGE #3: for LLM intent
from src.config import OPENAI_API_KEY, MODEL_NAME
from src.rag_chain import build_rag_chain
from src.guardrails import sanitize_input, sanitize_output
from src.models import Reservation, ReservationCreate            # ✅ CHANGE #6
from src.dynamic_db import (
    save_reservation, get_reservation,
    get_pending_reservations, update_reservation_status
)
from src.mcp_client import call_write_reservation

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7


# ── Shared state ──────────────────────────────────────────────────────

class PipelineState(TypedDict, total=False):
    user_message: str
    intent: str
    response: str
    reservation: Optional[dict]
    reservation_id: Optional[int]
    guardrail_triggered: bool
    mode: str
    admin_action: Optional[str]
    admin_comment: str
    admin_reservation_id: Optional[int]
    pipeline_step: str


# ── Reservation fields ────────────────────────────────────────────────

FIELDS = ["first_name", "last_name", "license_plate", "start_time", "end_time"]
PROMPTS = {
    "first_name": "Sure! What is your **first name**?",
    "last_name": "What is your **last name**?",
    "license_plate": "What is your **vehicle license plate** number?",
    "start_time": "When should the reservation **start**? (e.g. 2025-07-01 09:00)",
    "end_time": "When should it **end**? (e.g. 2025-07-01 18:00)",
}

BOOKING_KEYWORDS = ["reserve", "book", "reservation", "booking"]
STATUS_KEYWORDS = ["status", "check reservation", "my reservation"]


def _next_missing(res: dict) -> Optional[str]:
    for f in FIELDS:
        if not res.get(f):
            return f
    return None


# ✅ CHANGE #3: LLM-based intent classification
def _llm_classify_intent(message: str) -> str:
    """Fallback: use LLM when keywords don't match."""
    try:
        llm = ChatOpenAI(model=MODEL_NAME, temperature=0, openai_api_key=OPENAI_API_KEY)
        result = llm.invoke(
            f"Classify this user message into exactly one category.\n"
            f"Categories: info, reservation, check_status\n"
            f"- info: asking questions about parking (prices, hours, location, policies)\n"
            f"- reservation: wants to book/reserve a parking spot\n"
            f"- check_status: asking about their existing reservation status\n\n"
            f"Message: \"{message}\"\n\n"
            f"Reply with ONLY the category name, nothing else."
        )
        intent = result.content.strip().lower()
        if intent in ("info", "reservation", "check_status"):
            logger.info("LLM classified '%s' → %s", message[:40], intent)    # ✅ CHANGE #7
            return intent
        logger.warning("LLM returned unexpected intent '%s', defaulting to info", intent)
        return "info"
    except Exception as e:
        logger.error("LLM intent classification failed: %s", e)              # ✅ CHANGE #7
        return "info"


# ── Build pipeline ────────────────────────────────────────────────────

def build_pipeline(vector_store, db_path=None):

    rag_ask = build_rag_chain(vector_store, db_path)

    # Node 1: Input guardrail
    def input_guard(state: PipelineState) -> PipelineState:
        cleaned, blocked = sanitize_input(state.get("user_message", ""))
        state["user_message"] = cleaned
        state["guardrail_triggered"] = blocked
        return state

    # Node 2: Route to correct handler
    # ✅ CHANGE #3: keyword matching as fast path, LLM as fallback
    def router(state: PipelineState) -> PipelineState:
        if state.get("mode") == "admin":
            state["intent"] = "admin"
            return state

        state["mode"] = "user"
        msg = state.get("user_message", "").lower()
        res = state.get("reservation")

        # Fast path 1: reservation in progress → keep collecting
        if res is not None and _next_missing(res):
            state["intent"] = "reservation"
            logger.debug("Router: reservation in progress")              # ✅ CHANGE #7
            return state

        # Fast path 2: keyword match for booking
        if any(w in msg for w in BOOKING_KEYWORDS):
            state["intent"] = "reservation"
            logger.debug("Router: keyword match → reservation")          # ✅ CHANGE #7
            return state

        # Fast path 3: keyword match for status check
        if any(w in msg for w in STATUS_KEYWORDS):
            state["intent"] = "check_status"
            logger.debug("Router: keyword match → check_status")         # ✅ CHANGE #7
            return state

        # ✅ CHANGE #3: No keyword matched → ask LLM to classify
        logger.debug("Router: no keyword match for '%s', using LLM", msg[:40])
        state["intent"] = _llm_classify_intent(msg)
        return state

    # Node 3: RAG answer
    def rag_node(state: PipelineState) -> PipelineState:
        result = rag_ask(state["user_message"])
        state["response"] = result["answer"]
        return state

    # Node 4: Collect reservation fields
    # ✅ CHANGE #6: uses ReservationCreate model for validation
    def reservation_node(state: PipelineState) -> PipelineState:
        res = state.get("reservation")
        msg = state.get("user_message", "").strip()

        if res is None:
            state["reservation"] = {}
            state["response"] = PROMPTS["first_name"]
            return state

        nf = _next_missing(res)
        if nf:
            res[nf] = msg

        nf = _next_missing(res)
        if nf:
            state["response"] = PROMPTS[nf]
        else:
            # ✅ CHANGE #6: validate with Pydantic before saving
            try:
                validated = ReservationCreate(**res)
            except Exception as e:
                logger.error("Reservation validation failed: %s", e)     # ✅ CHANGE #7
                state["response"] = f"Invalid data: {e}. Let's start over."
                state["reservation"] = None
                return state

            saved = save_reservation(validated, db_path)
            state["response"] = (
                f"✅ Reservation submitted (#{saved.id})!\n"
                f"• Name: {saved.full_name}\n"                           # ✅ CHANGE #6: model property
                f"• Plate: {saved.license_plate}\n"
                f"• Period: {saved.start_time} → {saved.end_time}\n\n"
                f"📨 Sent to admin for approval.\n"
                f"Ask **check my reservation** to see status."
            )
            state["reservation_id"] = saved.id
            state["reservation"] = None
        return state

    # Node 5: Check reservation status
    # ✅ CHANGE #6: uses Reservation model
    def check_status_node(state: PipelineState) -> PipelineState:
        rid = state.get("reservation_id")
        if not rid:
            state["response"] = "No reservation on file. Want to make one?"
            return state
        r = get_reservation(rid, db_path)        # ✅ returns Reservation or None
        if not r:
            state["response"] = "Reservation not found."
        elif r.status == "approved":             # ✅ CHANGE #6: dot access, not dict
            state["response"] = f"✅ Reservation #{rid} **approved**!"
            if r.admin_comment:
                state["response"] += f"\nAdmin note: {r.admin_comment}"
        elif r.status == "rejected":
            state["response"] = f"❌ Reservation #{rid} **rejected**."
            if r.admin_comment:
                state["response"] += f"\nReason: {r.admin_comment}"
        else:
            state["response"] = f"⏳ Reservation #{rid} still **pending**."
        return state

    # Node 6: Admin approve / reject
    # ✅ CHANGE #6: uses Reservation model
    def admin_node(state: PipelineState) -> PipelineState:
        action = state.get("admin_action")
        rid = state.get("admin_reservation_id")
        comment = state.get("admin_comment", "")

        if not rid or not action:
            pending = get_pending_reservations(db_path)    # ✅ returns List[Reservation]
            if not pending:
                state["response"] = "No pending reservations."
            else:
                lines = [f"{len(pending)} pending:"]
                for r in pending:
                    lines.append(
                        f"  #{r.id} | {r.full_name} "     # ✅ CHANGE #6: model properties
                        f"| {r.license_plate} | {r.start_time} → {r.end_time}"
                    )
                state["response"] = "\n".join(lines)
            state["pipeline_step"] = "admin_list"
            return state

        if action == "approve":
            updated = update_reservation_status(rid, "approved", comment, db_path)
            if updated:
                state["response"] = f"✅ #{rid} approved."
                state["admin_reservation_id"] = rid
                state["pipeline_step"] = "admin_approved"
            else:
                state["response"] = "Not found."
                state["pipeline_step"] = "admin_done"
        elif action == "reject":
            updated = update_reservation_status(rid, "rejected", comment, db_path)
            state["response"] = f"❌ #{rid} rejected." if updated else "Not found."
            state["pipeline_step"] = "admin_done"
        else:
            state["response"] = "Unknown action."
            state["pipeline_step"] = "admin_done"
        return state

    # Node 7: MCP write
    # ✅ CHANGE #6: passes Reservation model to MCP client
    def mcp_node(state: PipelineState) -> PipelineState:
        rid = state.get("admin_reservation_id")
        if rid:
            r = get_reservation(rid, db_path)    # ✅ returns Reservation model
            if r and r.status == "approved":
                result = call_write_reservation(r)    # ✅ CHANGE #6: model, not dict
                msg = result.get("message", "Written to file.")
                if result.get("success"):
                    state["response"] += f"\n📝 {msg}"
                else:
                    state["response"] += f"\n⚠️ {msg}"  # ✅ CHANGE #2: show failure
        return state

    # Node 8: Output guardrail
    def output_guard(state: PipelineState) -> PipelineState:
        cleaned, had_sensitive = sanitize_output(state.get("response", ""))
        state["response"] = cleaned
        if had_sensitive:
            state["guardrail_triggered"] = True
        return state

    # Routing
    def route_intent(state: PipelineState) -> str:
        return state.get("intent", "info")

    def route_after_admin(state: PipelineState) -> str:
        return "write_file" if state.get("pipeline_step") == "admin_approved" else "done"

    # Build graph
    g = StateGraph(PipelineState)
    g.add_node("input_guard", input_guard)
    g.add_node("router", router)
    g.add_node("rag", rag_node)
    g.add_node("reservation", reservation_node)
    g.add_node("check_status", check_status_node)
    g.add_node("admin", admin_node)
    g.add_node("mcp_write", mcp_node)
    g.add_node("output_guard", output_guard)

    g.set_entry_point("input_guard")
    g.add_edge("input_guard", "router")
    g.add_conditional_edges("router", route_intent, {
        "info": "rag",
        "reservation": "reservation",
        "check_status": "check_status",
        "admin": "admin",
    })
    g.add_edge("rag", "output_guard")
    g.add_edge("reservation", "output_guard")
    g.add_edge("check_status", "output_guard")
    g.add_conditional_edges("admin", route_after_admin, {
        "write_file": "mcp_write",
        "done": "output_guard",
    })
    g.add_edge("mcp_write", "output_guard")
    g.add_edge("output_guard", END)

    return g.compile()