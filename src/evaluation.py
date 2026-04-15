"""RAG evaluation: tests full pipeline (retrieval + LLM answer), not just retrieval."""

import time
import logging                                                   # ✅ CHANGE #7
from src.rag_chain import build_rag_chain

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7

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


# ✅ CHANGE #4: evaluates FULL RAG pipeline (retrieval + LLM answer)
def evaluate_retrieval(vector_store, db_path=None, k=3):
    rag_ask = build_rag_chain(vector_store, db_path)       # ✅ CHANGE #4: full chain, not just search

    results = []
    for item in EVAL_DATASET:
        t0 = time.perf_counter()
        rag_result = rag_ask(item["question"])              # ✅ CHANGE #4: calls full chain
        latency = (time.perf_counter() - t0) * 1000

        # Retrieval metrics: check if context contains keywords
        retrieved = rag_result["retrieved_docs"]
        context_text = " ".join(retrieved).lower()
        expected = item["expected_keywords"]
        context_hits = sum(1 for kw in expected if kw.lower() in context_text)
        retrieval_recall = context_hits / len(expected) if expected else 0

        # ✅ CHANGE #4: Answer metrics: check if FINAL ANSWER contains keywords
        answer_text = rag_result["answer"].lower()
        answer_hits = sum(1 for kw in expected if kw.lower() in answer_text)
        answer_recall = answer_hits / len(expected) if expected else 0

        # Precision: how many retrieved chunks were relevant
        relevant = sum(1 for t in retrieved
                       if any(kw.lower() in t.lower() for kw in expected))
        precision = relevant / len(retrieved) if retrieved else 0

        results.append({
            "question": item["question"],
            "retrieval_recall": round(retrieval_recall, 3),
            "answer_recall": round(answer_recall, 3),       # ✅ CHANGE #4: new metric
            "precision": round(precision, 3),
            "latency_ms": round(latency, 1),
        })
        logger.debug("Eval: %s → R=%.2f A=%.2f",
                      item["question"][:30], retrieval_recall, answer_recall)  # ✅ CHANGE #7

    avg = lambda key: round(sum(r[key] for r in results) / len(results), 3)
    return {
        "num_questions": len(results),
        "top_k": k,
        "avg_retrieval_recall": avg("retrieval_recall"),
        "avg_answer_recall": avg("answer_recall"),           # ✅ CHANGE #4: new metric
        "avg_precision": avg("precision"),
        "avg_latency_ms": round(avg("latency_ms"), 1),
        "details": results,
    }


def print_report(report):
    print("\n" + "=" * 65)
    print("       RAG EVALUATION REPORT")
    print("=" * 65)
    print(f"  Questions        : {report['num_questions']}")
    print(f"  Top-K            : {report['top_k']}")
    print(f"  Retrieval Recall : {report['avg_retrieval_recall']:.3f}")
    print(f"  Answer Recall    : {report['avg_answer_recall']:.3f}")  # ✅ CHANGE #4
    print(f"  Precision        : {report['avg_precision']:.3f}")
    print(f"  Latency          : {report['avg_latency_ms']:.1f} ms")
    print("-" * 65)
    for r in report["details"]:
        # ✅ CHANGE #4: show both retrieval and answer recall
        r_ok = "✅" if r["retrieval_recall"] == 1.0 else "⚠️"
        a_ok = "✅" if r["answer_recall"] == 1.0 else "⚠️"
        print(f"  {r_ok}{a_ok} {r['question']}")
        print(f"      Retrieval R={r['retrieval_recall']:.3f}  "
              f"Answer R={r['answer_recall']:.3f}  "
              f"P={r['precision']:.3f}  {r['latency_ms']:.0f}ms")
    print("=" * 65)