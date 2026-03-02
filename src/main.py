"""Entry point: chat, admin, api, or evaluation."""

import sys
from src.loader import load_static_documents
from src.vectorstore import ingest_documents
from src.dynamic_db import init_db
from src.chatbot import build_chatbot
from src.evaluation import evaluate_retrieval, print_report
from src.admin_agent import get_pending_list, approve_reservation, reject_reservation
from src.dynamic_db import get_reservation


def setup():
    print("Loading data...")
    docs = load_static_documents()
    vector_store = ingest_documents(docs)
    init_db()
    print("Ready!\n")
    return vector_store


def run_chat():
    vector_store = setup()
    chatbot = build_chatbot(vector_store)

    print("🅿️  CityCenter Smart Parking Chatbot")
    print("Type 'quit' to exit.\n")

    session = {}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        session["user_message"] = user_input
        result = chatbot.invoke(session)

        session = {
            "reservation": result.get("reservation"),
            "reservation_id": result.get("reservation_id"),
        }

        print(f"\nBot: {result.get('response', 'Sorry, something went wrong.')}")
        if result.get("guardrail_triggered"):
            print("  ⚠️  [Guardrail triggered]")
        print()


def run_admin():
    setup()

    print("🔧 Admin Panel")
    print("Commands: list | approve <id> | reject <id> | view <id> | quit\n")

    while True:
        try:
            cmd = input("Admin> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not cmd:
            continue
        if cmd in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        parts = cmd.split()

        if parts[0] == "list":
            pending = get_pending_list()
            if not pending:
                print("  No pending reservations.\n")
            else:
                print(f"  {len(pending)} pending:\n")
                for r in pending:
                    print(f"  #{r['id']} | {r['first_name']} {r['last_name']} "
                          f"| {r['license_plate']} | {r['start_time']} → {r['end_time']}")
                print()

        elif parts[0] == "view" and len(parts) == 2:
            res = get_reservation(int(parts[1]))
            if not res:
                print("  Not found.\n")
            else:
                print(f"  #{res['id']}: {res['first_name']} {res['last_name']}")
                print(f"  Plate: {res['license_plate']}")
                print(f"  Period: {res['start_time']} → {res['end_time']}")
                print(f"  Status: {res['status']}")
                print(f"  Comment: {res.get('admin_comment', '')}\n")

        elif parts[0] == "approve" and len(parts) >= 2:
            comment = " ".join(parts[2:]) if len(parts) > 2 else ""
            updated = approve_reservation(int(parts[1]), comment)
            if updated:
                print(f"  ✅ Reservation #{parts[1]} approved.\n")
            else:
                print("  Not found.\n")

        elif parts[0] == "reject" and len(parts) >= 2:
            comment = " ".join(parts[2:]) if len(parts) > 2 else ""
            updated = reject_reservation(int(parts[1]), comment)
            if updated:
                print(f"  ❌ Reservation #{parts[1]} rejected.\n")
            else:
                print("  Not found.\n")

        else:
            print("  Unknown command. Use: list | view <id> | approve <id> | reject <id>\n")


def run_api():
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)


def run_eval():
    vector_store = setup()
    report = evaluate_retrieval(vector_store)
    print_report(report)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "chat"

    if mode == "api":
        run_api()
    elif mode == "admin":
        run_admin()
    elif mode == "eval":
        run_eval()
    else:
        run_chat()