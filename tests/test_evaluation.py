from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


def test_eval_dataset_valid():
    from src.evaluation import EVAL_DATASET
    assert len(EVAL_DATASET) == 10
    for item in EVAL_DATASET:
        assert "question" in item
        assert len(item["expected_keywords"]) > 0


def test_report_structure():
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="CityCenter at 123 Main Street Metropolis. EV charging."),
        Document(page_content="Hours: monday 06-23. Hourly $5. Monthly $400."),
        Document(page_content="Payment: Credit Card, Cash. I-90 Exit 12B. Height 2.1m."),
    ]
    with patch("src.evaluation.get_dynamic_context",
               return_value="saturday: 07:00 - 22:00\nhourly: 5.0\nL2: 80/80"):
        from src.evaluation import evaluate_retrieval
        report = evaluate_retrieval(mock_store, db_path=":memory:")
    assert "avg_recall_at_k" in report
    assert "avg_precision_at_k" in report
    assert len(report["details"]) == 10
    assert all(0 <= r["recall_at_k"] <= 1 for r in report["details"])