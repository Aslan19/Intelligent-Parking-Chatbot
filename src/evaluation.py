"""RAG evaluation: Recall@K, Precision@K, latency."""

import time
from src.vectorstore import search
from src.dynamic_db import get_dynamic_context

EVAL_DATASET = [
    {"question": "What is the address of the parking?",
     "expected_keywords": ["123 Main Street", "Metropolis"]},
    {"question": "What are the working hours on Saturday?",
     "expected_keywords": ["07:00", "22:00", "saturday"]},
    {"question": "How much does hourly parking cost?",
     "expected_keywords": ["5"]},
    {"question": "Is EV charging available?",
     "expected_keywords": ["EV charging", "electric vehicle"]},
    {"question": "What payment methods do you accept?",
     "expected_keywords": ["Credit Card", "Cash"]},
    {"question": "How do I get there from the highway?",
     "expected_keywords": ["I-90", "Exit 12B"]},
    {"question": "How much is the monthly pass?",
     "expected_keywords": ["400"]},
    {"question": "What is the maximum vehicle height?",
     "expected_keywords": ["2.1"]},
    {"question": "How many spaces does Level L2 have?",
     "expected_keywords": ["80"]},
    {"question": "How do I make a reservation?",
     "expected_keywords": ["first name", "last name", "license plate"]},
]


def evaluate_retrieval(vector_store, db_path=None, k=3):
    results = []
    for item in EVAL_DATASET:
        t0 = time.perf_counter()
        docs = search(vector_store, item["question"], k=k)
        latency = (time.perf_counter() - t0) * 1000

        retrieved = [d.page_content for d in docs]
        dynamic = get_dynamic_context(db_path)
        combined = " ".join(retrieved + [dynamic]).lower()

        expected = item["expected_keywords"]
        hits = sum(1 for kw in expected if kw.lower() in combined)
        recall = hits / len(expected) if expected else 0

        all_ctx = retrieved + [dynamic]
        relevant = sum(1 for t in all_ctx if any(kw.lower() in t.lower() for kw in expected))
        precision = relevant / len(all_ctx) if all_ctx else 0

        results.append({
            "question": item["question"],
            "recall_at_k": round(recall, 3),
            "precision_at_k": round(precision, 3),
            "latency_ms": round(latency, 1),
        })

    avg = lambda key: round(sum(r[key] for r in results) / len(results), 3)
    return {
        "num_questions": len(results),
        "top_k": k,
        "avg_recall_at_k": avg("recall_at_k"),
        "avg_precision_at_k": avg("precision_at_k"),
        "avg_latency_ms": round(avg("latency_ms"), 1),
        "details": results,
    }


def print_report(report):
    print("\n" + "=" * 60)
    print("       RAG EVALUATION REPORT")
    print("=" * 60)
    print(f"  Questions  : {report['num_questions']}")
    print(f"  Top-K      : {report['top_k']}")
    print(f"  Recall@K   : {report['avg_recall_at_k']:.3f}")
    print(f"  Precision@K: {report['avg_precision_at_k']:.3f}")
    print(f"  Latency    : {report['avg_latency_ms']:.1f} ms")
    print("-" * 60)
    for r in report["details"]:
        status = "✅" if r["recall_at_k"] == 1.0 else "⚠️"
        print(f"  {status} {r['question']}")
        print(f"     R={r['recall_at_k']:.3f}  P={r['precision_at_k']:.3f}  {r['latency_ms']:.0f}ms")
    print("=" * 60)