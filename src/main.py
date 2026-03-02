"""Entry point: run the chatbot interactively or run evaluation."""

import sys
from src.loader import load_static_documents
from src.vectorstore import ingest_documents
from src.dynamic_db import init_db
from src.chatbot import build_chatbot
from src.evaluation import evaluate_retrieval, print_report


def setup():
    """Initialize vector store and SQL database. Returns vector_store."""
    print("Loading data and building indexes...")
    docs = load_static_documents()
    vector_store = ingest_documents(docs)
    init_db()
    print(f"Loaded {len(docs)} static documents into ChromaDB.")
    print("Dynamic data loaded into SQLite.")
    return vector_store


def run_chat():
    """Interactive CLI chatbot."""
    vector_store = setup()
    chatbot = build_chatbot(vector_store)

    print("\n🅿️  CityCenter Smart Parking Chatbot")
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

        # Carry reservation state across turns
        session["user_message"] = user_input
        result = chatbot.invoke(session)

        # Preserve reservation state for next turn
        session = {"reservation": result.get("reservation", {})}

        print(f"\nBot: {result.get('response', 'Sorry, I could not process that.')}")
        if result.get("guardrail_triggered"):
            print("  ⚠️  [Guardrail was triggered on this exchange]")
        print()


def run_eval():
    """Run RAG evaluation and print report."""
    vector_store = setup()
    report = evaluate_retrieval(vector_store)
    print_report(report)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_eval()
    else:
        run_chat()