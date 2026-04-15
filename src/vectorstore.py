"""ChromaDB vector store for static parking data."""

import logging                                                   # ✅ CHANGE #7
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config import CHROMA_DIR, EMBEDDING_MODEL, OPENAI_API_KEY, TOP_K

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7


def create_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)


def ingest_documents(documents, persist_dir=None):
    # ✅ CHANGE #8: try/except around ChromaDB initialization
    try:
        store = Chroma.from_documents(
            documents=documents,
            embedding=create_embeddings(),
            persist_directory=persist_dir or CHROMA_DIR,
            collection_name="parking"
        )
        logger.info("ChromaDB ingested %d documents", len(documents))    # ✅ CHANGE #7
        return store
    except Exception as e:
        logger.critical("ChromaDB initialization failed: %s", e)         # ✅ CHANGE #7
        raise RuntimeError(f"ChromaDB failed to initialize: {e}") from e # ✅ CHANGE #8


def search(store, query, k=None):
    # ✅ CHANGE #8: try/except around similarity search
    try:
        results = store.similarity_search(query, k=k or TOP_K)
        logger.debug("Search for '%s' returned %d results", query, len(results))  # ✅ CHANGE #7
        return results
    except Exception as e:
        logger.error("ChromaDB search failed: %s", e)                             # ✅ CHANGE #7
        return []                                                                  # ✅ CHANGE #8