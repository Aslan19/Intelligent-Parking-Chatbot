import os
import sys
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 3

_root = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(_root, "data", "parking_info.json")
CHROMA_DIR = os.path.join(_root, "chroma_db")
SQLITE_PATH = os.path.join(_root, "dynamic_data.db")

# ✅ MCP: stdio transport — client spawns server as subprocess
MCP_SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "mcp_server.py")
MCP_OUTPUT_FILE = os.getenv("MCP_OUTPUT_FILE",
    os.path.join(_root, "confirmed_reservations.txt"))

# ✅ Removed: MCP_HOST, MCP_PORT, MCP_BASE_URL, MCP_API_KEY (not needed for stdio)
MCP_FALLBACK_ENABLED = os.getenv("MCP_FALLBACK_ENABLED", "false").lower() == "true"