"""Load static parking data from JSON into LangChain Documents."""

import json
import logging                                                   # ✅ CHANGE #7
from langchain_core.documents import Document
from src.config import DATA_PATH

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7


def load_static_documents(data_path=None):
    raw = json.loads(open(data_path or DATA_PATH).read())
    docs = [
        Document(page_content=item["text"], metadata={"id": item["id"]})
        for item in raw["static"]
    ]
    logger.info("Loaded %d static documents", len(docs))         # ✅ CHANGE #7
    return docs