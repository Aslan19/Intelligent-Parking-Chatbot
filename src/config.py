import os
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

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
MCP_API_KEY = os.getenv("MCP_API_KEY", "mcp-secret-key-123")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", f"http://localhost:{MCP_PORT}")
MCP_OUTPUT_FILE = os.getenv("MCP_OUTPUT_FILE",
    os.path.join(_root, "confirmed_reservations.txt"))