"""ChromaDB vector store: ingest static documents and search."""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config import CHROMA_DIR, EMBEDDING_MODEL, OPENAI_API_KEY, TOP_K


def create_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)


def ingest_documents(documents, persist_dir=None):
    """Store documents in ChromaDB. Returns the Chroma instance."""
    store = Chroma.from_documents(
        documents=documents,
        embedding=create_embeddings(),
        persist_directory=persist_dir or CHROMA_DIR,
        collection_name="parking"
    )
    return store


def load_store(persist_dir=None):
    """Load existing ChromaDB store."""
    return Chroma(
        persist_directory=persist_dir or CHROMA_DIR,
        embedding_function=create_embeddings(),
        collection_name="parking"
    )


def search(store, query, k=None):
    """Return top-k similar documents."""
    return store.similarity_search(query, k=k or TOP_K)