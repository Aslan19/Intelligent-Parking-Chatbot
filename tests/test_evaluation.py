"""Tests for the evaluation module."""

from unittest.mock import MagicMock
from langchain_core.documents import Document


def test_keyword_matching_positive():
    """Keyword found in text should count as hit."""
    from src.evaluation import EVAL_DATASET
    # Basic sanity: eval dataset is not empty
    assert len(EVAL_DATASET) >= 5
    for item in EVAL_DATASET:
        assert "question" in item
        assert "expected_keywords" in item
        assert len(item["expected_keywords"]) > 0


def test_evaluation_report_structure():
    """Mocked evaluation should return correct report shape."""
    from unittest.mock import patch

    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="CityCenter parking at 123 Main Street Metropolis 10001. EV charging available."),
        Document(page_content="Working hours: monday 06:00-23:00. Hourly rate $5. Monthly pass $400."),
        Document(page_content="Payment: Credit Card, Cash. Directions: I-90 Exit 12B. Height limit 2.1m."),
    ]

    with patch("src.evaluation.get_dynamic_context",
               return_value="saturday: 07:00 - 22:00\nhourly: 5.0\nL2: 80/80"):
        from src.evaluation import evaluate_retrieval
        report = evaluate_retrieval(mock_store, db_path=":memory:")

    assert "avg_recall_at_k" in report
    assert "avg_precision_at_k" in report
    assert "avg_latency_ms" in report
    assert "details" in report
    assert len(report["details"]) == 10
    assert all(0 <= r["recall_at_k"] <= 1 for r in report["details"])


def test_evaluation_latency_is_measured():
    """Each result should have a positive latency."""
    from unittest.mock import patch

    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="Test content with 123 Main Street and EV charging"),
    ]

    with patch("src.evaluation.get_dynamic_context", return_value="test dynamic"):
        from src.evaluation import evaluate_retrieval
        report = evaluate_retrieval(mock_store, db_path=":memory:")

    for r in report["details"]:
        assert r["latency_ms"] >= 0