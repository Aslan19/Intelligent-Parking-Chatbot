"""Entry point: chat | admin | eval"""

import sys
import logging
from src.loader import load_static_documents
from src.vectorstore import ingest_documents
from src.dynamic_db import init_db, get_reservation
from src.orchestrator import build_pipeline
from src.evaluation import evaluate_retrieval, print_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def setup():
    logger.info("Loading data...")
    docs = load_static_documents()
    vs = ingest_documents(docs)
    init_db()
    logger.info("System ready")
    return vs


def run_chat():
    pipeline = build_pipeline(setup())
    print("🅿️  CityCenter Smart Parking — Type 'quit' to exit.\n")
    session = {}

    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        if msg.lower() in ("quit", "exit", "q"):
            break

        session["user_message"] = msg
        session["mode"] = "user"
        result = pipeline.invoke(session)
        session = {"reservation": result.get("reservation"),
                   "reservation_id": result.get("reservation_id")}

        print(f"\nBot: {result.get('response', 'Error.')}")
        if result.get("guardrail_triggered"):
            print("  ⚠️  [Guardrail triggered]")
        print()
    print("Goodbye!")


def run_admin():
    pipeline = build_pipeline(setup())
    print("🔧 Admin — Commands: list | view <id> | approve <id> [comment] | reject <id> [comment] | quit\n")

    while True:
        try:
            cmd = input("Admin> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit", "q"):
            break

        parts = cmd.split()
        state = {"mode": "admin", "user_message": ""}

        if parts[0] == "list":
            pass
        elif parts[0] == "view" and len(parts) == 2:
            r = get_reservation(int(parts[1]))
            if not r:
                print("  Not found.\n")
            else:
                print(f"  #{r.id}: {r.full_name}")
                print(f"  Plate: {r.license_plate}")
                print(f"  Period: {r.start_time} → {r.end_time}")
                print(f"  Status: {r.status}")
                if r.admin_comment:
                    print(f"  Comment: {r.admin_comment}")
                print()
            continue
        elif parts[0] in ("approve", "reject") and len(parts) >= 2:
            state["admin_action"] = parts[0]
            state["admin_reservation_id"] = int(parts[1])
            state["admin_comment"] = " ".join(parts[2:]) if len(parts) > 2 else ""
        else:
            print("  Unknown. Use: list | view <id> | approve <id> | reject <id>\n")
            continue

        result = pipeline.invoke(state)
        print(f"  {result.get('response', '')}\n")

    print("Goodbye!")


def run_eval():
    report = evaluate_retrieval(setup())
    print_report(report)


if __name__ == "__main__":
    modes = {"chat": run_chat, "admin": run_admin, "eval": run_eval}
    mode = sys.argv[1] if len(sys.argv) > 1 else "chat"
    if mode in modes:
        modes[mode]()
    else:
        print(f"Usage: python -m src.main [{' | '.join(modes)}]")