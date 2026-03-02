import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "parking_info.json")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "dynamic_data.db")
TOP_K = 3