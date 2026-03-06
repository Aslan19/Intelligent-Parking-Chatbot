"""ChromaDB vector store for static parking data."""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config import CHROMA_DIR, EMBEDDING_MODEL, OPENAI_API_KEY, TOP_K


def create_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)


def ingest_documents(documents, persist_dir=None):
    return Chroma.from_documents(
        documents=documents,
        embedding=create_embeddings(),
        persist_directory=persist_dir or CHROMA_DIR,
        collection_name="parking"
    )


def search(store, query, k=None):
    return store.similarity_search(query, k=k or TOP_K)