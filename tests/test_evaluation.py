"""Evaluation tests — now checks answer_recall metric."""

from unittest.mock import MagicMock, patch


def test_eval_dataset_valid():
    from src.evaluation import EVAL_DATASET
    assert len(EVAL_DATASET) == 10
    for item in EVAL_DATASET:
        assert "question" in item
        assert len(item["expected_keywords"]) > 0


def test_report_has_answer_recall():
    mock_rag = MagicMock()
    mock_rag.return_value = {
        "answer": "Parking at 123 Main Street Metropolis. Hourly $5. EV charging available.",
        "retrieved_docs": [
            "CityCenter at 123 Main Street Metropolis.",
            "Payment: Credit Card, Cash. I-90 Exit 12B.",
            "Height 2.1m. Monthly $400. Saturday 07:00-22:00.",
        ],
        "latency_ms": 42.0
    }

    with patch("src.evaluation.build_rag_chain", return_value=mock_rag):
        from src.evaluation import evaluate_retrieval
        report = evaluate_retrieval(MagicMock(), db_path=":memory:")

    assert "avg_retrieval_recall" in report
    assert "avg_answer_recall" in report
    assert "avg_precision" in report
    assert len(report["details"]) == 10

    for r in report["details"]:
        assert "retrieval_recall" in r
        assert "answer_recall" in r 
        assert 0 <= r["answer_recall"] <= 1