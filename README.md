# 🅿️ Parking Chatbot

RAG-based chatbot for parking information and reservations.

## Architecture

```
User Message
     │
     ▼
┌─────────────┐
│ Input Guard  │  ← blocks prompt injection
├─────────────┤
│ Classifier   │  ← "info" or "reservation"
├──────┬──────┤
│      │      │
▼      │      ▼
RAG    │   Reservation
Info   │   Collector
│      │      │
│  ChromaDB   │  SQLite
│  (static)   │  (dynamic + reservations)
├──────┴──────┤
│ Output Guard │  ← redacts sensitive data
└─────────────┘
     │
     ▼
  Response
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
```

## Run

```bash
# Interactive chat
python -m src.main

# Run evaluation
python -m src.main eval
```

## Run Tests

```bash
pytest tests/ -v
```

## Files

| File | Purpose |
|------|---------|
| `src/config.py` | Settings from .env |
| `src/loader.py` | Load static docs from JSON |
| `src/dynamic_db.py` | SQLite for hours/prices/availability |
| `src/vectorstore.py` | ChromaDB vector store |
| `src/rag_chain.py` | RAG: retrieve + LLM answer |
| `src/guardrails.py` | Input/output safety filters |
| `src/chatbot.py` | LangGraph conversation flow |
| `src/evaluation.py` | Recall@K, Precision@K metrics |
| `src/main.py` | Entry point |