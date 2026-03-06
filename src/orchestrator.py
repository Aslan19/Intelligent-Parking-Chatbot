"""Unified LangGraph pipeline: user chat + admin approval + MCP file write."""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from src.rag_chain import build_rag_chain
from src.guardrails import sanitize_input, sanitize_output
from src.dynamic_db import (
    save_reservation, get_reservation,
    get_pending_reservations, update_reservation_status
)
from src.mcp_client import call_write_reservation


# ── Shared state ──────────────────────────────────────────────────────

class PipelineState(TypedDict, total=False):
    user_message: str
    intent: str
    response: str
    reservation: Optional[dict]
    reservation_id: Optional[int]
    guardrail_triggered: bool
    mode: str                          # "user" | "admin"
    admin_action: Optional[str]        # "approve" | "reject"
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


def _next_missing(res: dict) -> Optional[str]:
    for f in FIELDS:
        if not res.get(f):
            return f
    return None


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
    def router(state: PipelineState) -> PipelineState:
        if state.get("mode") == "admin":
            state["intent"] = "admin"
            return state

        state["mode"] = "user"
        msg = state.get("user_message", "").lower()
        res = state.get("reservation")

        if res is not None and _next_missing(res):
            state["intent"] = "reservation"
        elif any(w in msg for w in ["status", "check reservation", "my reservation"]):
            state["intent"] = "check_status"
        elif any(w in msg for w in ["reserve", "book", "reservation", "booking"]):
            state["intent"] = "reservation"
        else:
            state["intent"] = "info"
        return state

    # Node 3: RAG answer
    def rag_node(state: PipelineState) -> PipelineState:
        result = rag_ask(state["user_message"])
        state["response"] = result["answer"]
        return state

    # Node 4: Collect reservation fields one by one
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
            rid = save_reservation(res, db_path)
            state["response"] = (
                f"✅ Reservation submitted (#{rid})!\n"
                f"• Name: {res['first_name']} {res['last_name']}\n"
                f"• Plate: {res['license_plate']}\n"
                f"• Period: {res['start_time']} → {res['end_time']}\n\n"
                f"📨 Sent to admin for approval.\n"
                f"Ask **check my reservation** to see status."
            )
            state["reservation_id"] = rid
            state["reservation"] = None
        return state

    # Node 5: Check reservation status
    def check_status_node(state: PipelineState) -> PipelineState:
        rid = state.get("reservation_id")
        if not rid:
            state["response"] = "No reservation on file. Want to make one?"
            return state
        r = get_reservation(rid, db_path)
        if not r:
            state["response"] = "Reservation not found."
        elif r["status"] == "approved":
            state["response"] = f"✅ Reservation #{rid} **approved**!"
            if r.get("admin_comment"):
                state["response"] += f"\nAdmin note: {r['admin_comment']}"
        elif r["status"] == "rejected":
            state["response"] = f"❌ Reservation #{rid} **rejected**."
            if r.get("admin_comment"):
                state["response"] += f"\nReason: {r['admin_comment']}"
        else:
            state["response"] = f"⏳ Reservation #{rid} still **pending**."
        return state

    # Node 6: Admin approve / reject
    def admin_node(state: PipelineState) -> PipelineState:
        action = state.get("admin_action")
        rid = state.get("admin_reservation_id")
        comment = state.get("admin_comment", "")

        if not rid or not action:
            pending = get_pending_reservations(db_path)
            if not pending:
                state["response"] = "No pending reservations."
            else:
                lines = [f"{len(pending)} pending:"]
                for r in pending:
                    lines.append(f"  #{r['id']} | {r['first_name']} {r['last_name']} "
                                 f"| {r['license_plate']} | {r['start_time']} → {r['end_time']}")
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

    # Node 7: MCP write to file
    def mcp_node(state: PipelineState) -> PipelineState:
        rid = state.get("admin_reservation_id")
        if rid:
            r = get_reservation(rid, db_path)
            if r and r["status"] == "approved":
                result = call_write_reservation(r)
                state["response"] += f"\n📝 {result.get('message', 'Written to file.')}"
        return state

    # Node 8: Output guardrail
    def output_guard(state: PipelineState) -> PipelineState:
        cleaned, had_sensitive = sanitize_output(state.get("response", ""))
        state["response"] = cleaned
        if had_sensitive:
            state["guardrail_triggered"] = True
        return state

    # Routing functions
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