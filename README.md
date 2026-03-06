# 🅿️ Parking Chatbot

RAG chatbot with admin approval and MCP file writing.

## Setup

```bash
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-your-key" > .env
```

## Run

```bash
python -m src.main mcp      # Terminal 1: MCP server
python -m src.main chat     # Terminal 2: user chat
python -m src.main admin    # Terminal 3: admin panel
python -m src.main eval     # evaluation report
pytest tests/ -v             # tests
```

## Demo

```
── User ──                         ── Admin ──
You: What are the prices?
Bot: Hourly \$5, daily \$30...

You: I want to book
Bot: First name?  → John
Bot: Last name?   → Doe
Bot: Plate?       → ABC-123
Bot: Start?       → 2025-07-01 09:00
Bot: End?         → 2025-07-01 17:00
Bot: ✅ Submitted (#1)!
                                   Admin> list
                                   Admin> approve 1 Spot B12
                                     ✅ Approved + written to file.
You: check my reservation
Bot: ✅ Approved! Note: Spot B12

── confirmed_reservations.txt ──
John Doe | ABC-123 | 2025-07-01 09:00 - 2025-07-01 17:00 | 2025-07-01 14:32:15
```