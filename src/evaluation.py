"""RAG evaluation: Recall@K, Precision@K, and latency measurement."""

import time
import json
from src.vectorstore import search
from src.dynamic_db import get_dynamic_context

# Test questions with expected keywords that MUST appear in retrieved context
EVAL_DATASET = [
    {
        "question": "What is the address of the parking?",
        "expected_keywords": ["123 Main Street", "Metropolis"]
    },
    {
        "question": "What are the working hours on Saturday?",
        "expected_keywords": ["07:00", "22:00", "saturday"]
    },
    {
        "question": "How much does hourly parking cost?",
        "expected_keywords": ["5"]
    },
    {
        "question": "Is EV charging available?",
        "expected_keywords": ["EV charging", "electric vehicle"]
    },
    {
        "question": "What payment methods do you accept?",
        "expected_keywords": ["Credit Card", "Cash"]
    },
    {
        "question": "How do I get there from the highway?",
        "expected_keywords": ["I-90", "Exit 12B"]
    },
    {
        "question": "How much is the monthly pass?",
        "expected_keywords": ["400"]
    },
    {
        "question": "What is the maximum vehicle height?",
        "expected_keywords": ["2.1"]
    },
    {
        "question": "How many spaces does Level L2 have?",
        "expected_keywords": ["80"]
    },
    {
        "question": "How do I make a reservation?",
        "expected_keywords": ["first name", "last name", "license plate"]
    }
]


def evaluate_retrieval(vector_store, db_path=None, k=3):
    """Run evaluation and return a report dict."""
    results = []

    for item in EVAL_DATASET:
        question = item["question"]
        expected = item["expected_keywords"]

        t0 = time.perf_counter()
        docs = search(vector_store, question, k=k)
        latency = (time.perf_counter() - t0) * 1000

        # Combine retrieved static docs + dynamic context for evaluation
        retrieved_texts = [d.page_content for d in docs]
        dynamic_text = get_dynamic_context(db_path)
        all_context = retrieved_texts + [dynamic_text]
        combined = " ".join(all_context).lower()

        # Recall@K: what fraction of expected keywords were found?
        hits = sum(1 for kw in expected if kw.lower() in combined)
        recall = hits / len(expected) if expected else 0

        # Precision@K: what fraction of retrieved chunks contain at least one keyword?
        relevant_chunks = sum(
            1 for text in all_context
            if any(kw.lower() in text.lower() for kw in expected)
        )
        precision = relevant_chunks / len(all_context) if all_context else 0

        results.append({
            "question": question,
            "expected_keywords": expected,
            "recall_at_k": round(recall, 3),
            "precision_at_k": round(precision, 3),
            "latency_ms": round(latency, 1)
        })

    avg_recall = sum(r["recall_at_k"] for r in results) / len(results)
    avg_precision = sum(r["precision_at_k"] for r in results) / len(results)
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)

    report = {
        "num_questions": len(results),
        "top_k": k,
        "avg_recall_at_k": round(avg_recall, 3),
        "avg_precision_at_k": round(avg_precision, 3),
        "avg_latency_ms": round(avg_latency, 1),
        "details": results
    }
    return report


def print_report(report):
    """Pretty-print the evaluation report."""
    print("\n" + "=" * 60)
    print("       RAG EVALUATION REPORT")
    print("=" * 60)
    print(f"  Questions tested : {report['num_questions']}")
    print(f"  Top-K            : {report['top_k']}")
    print(f"  Avg Recall@K     : {report['avg_recall_at_k']:.3f}")
    print(f"  Avg Precision@K  : {report['avg_precision_at_k']:.3f}")
    print(f"  Avg Latency      : {report['avg_latency_ms']:.1f} ms")
    print("-" * 60)

    for r in report["details"]:
        print(f"\n  Q: {r['question']}")
        print(f"    Recall@K  : {r['recall_at_k']:.3f}")
        print(f"    Precision : {r['precision_at_k']:.3f}")
        print(f"    Latency   : {r['latency_ms']:.1f} ms")

    print("\n" + "=" * 60)