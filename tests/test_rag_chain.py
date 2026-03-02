"""Tests for RAG chain (mocked - no real API calls)."""

from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


def test_rag_retrieves_relevant_docs():
    """Verify the chain uses vector search results."""
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="Parking at 123 Main Street, Metropolis."),
        Document(page_content="Open Monday-Friday 06:00-23:00."),
    ]

    from src.vectorstore import search
    results = search(mock_store, "What is the address?", k=2)
    assert len(results) == 2
    assert "123 Main Street" in results[0].page_content


def test_rag_chain_returns_expected_keys():
    """Verify build_rag_chain returns function producing correct dict shape."""
    with patch("src.rag_chain.ChatOpenAI") as MockLLM, \
         patch("src.rag_chain.get_dynamic_context", return_value="hours: 06-23"), \
         patch("src.rag_chain.search") as mock_search:

        mock_search.return_value = [
            Document(page_content="Parking at 123 Main Street.")
        ]

        # Mock the LLM chain
        mock_llm = MockLLM.return_value
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "The address is 123 Main Street."

        mock_store = MagicMock()

        from src.rag_chain import build_rag_chain
        ask = build_rag_chain(mock_store)

        # Patch the chain invocation inside the closure
        with patch("src.rag_chain.prompt") as mock_prompt:
            mock_pipe = MagicMock()
            mock_pipe.invoke.return_value = "The address is 123 Main Street."
            mock_prompt.__or__ = MagicMock(return_value=MagicMock(__or__=MagicMock(return_value=mock_pipe)))

            result = ask("What is the address?")
            assert "answer" in result
            assert "latency_ms" in result
            assert "retrieved_docs" in result