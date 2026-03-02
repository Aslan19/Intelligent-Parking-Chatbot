"""Load static parking data from JSON into LangChain Documents."""

import json
from langchain_core.documents import Document
from src.config import DATA_PATH


def load_static_documents(data_path=None):
    """Read the 'static' array from JSON, return list of Documents."""
    raw = json.loads(open(data_path or DATA_PATH).read())
    docs = []
    for item in raw["static"]:
        docs.append(Document(
            page_content=item["text"],
            metadata={"id": item["id"]}
        ))
    return docs