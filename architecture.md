# Architecture

## System Diagram

```
┌──────────────────────────────────────────────────────┐
│              LangGraph Pipeline                       │
│                                                       │
│  input_guard → router ──┬── rag ──────────┐          │
│                         ├── reservation ──┤          │
│                         ├── check_status ─┤          │
│                         └── admin ─┬──────┤          │
│                                    │      │          │
│                                mcp_write  │          │
│                                    │      │          │
│                                    └──┬───┘          │
│                                       │              │
│                                 output_guard → END   │
└───────────┬──────────┬────────────────┬──────────────┘
            │          │                │
        ChromaDB    SQLite        MCP Server
        (static)   (dynamic +     (port 8001)
                   reservations)       │
                                  text file
```

## Nodes

| Node | Trigger | Action |
|------|---------|--------|
| input_guard | Every message | Block prompt injections |
| router | After guard | Classify intent |
| rag | intent=info | Vector search + LLM answer |
| reservation | intent=reservation | Collect fields one by one |
| check_status | intent=check_status | Query reservation status |
| admin | mode=admin | Approve/reject reservations |
| mcp_write | After approval | Write to file via MCP server |
| output_guard | Before response | Redact sensitive data |

## Data Split

| Type | Storage | Examples |
|------|---------|----------|
| Static | ChromaDB | Address, policies, directions |
| Dynamic | SQLite | Hours, prices, availability |
| Reservations | SQLite → MCP → File | Booking records |

## Security

| Layer | Method |
|-------|--------|
| Input | Regex injection detection |
| Output | SSN/password/key redaction |
| MCP | API key authentication |