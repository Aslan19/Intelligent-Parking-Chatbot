"""Load static parking data from JSON into LangChain Documents."""

import json
from langchain_core.documents import Document
from src.config import DATA_PATH


def load_static_documents(data_path=None):
    raw = json.loads(open(data_path or DATA_PATH).read())
    return [
        Document(page_content=item["text"], metadata={"id": item["id"]})
        for item in raw["static"]
    ]