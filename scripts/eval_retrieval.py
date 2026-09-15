"""
Evaluate retrieval hit rate against data/eval_questions.json.

Run: python scripts/eval_retrieval.py
Writes: reports/retrieval_eval.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval_questions.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "retrieval_eval.json"

sys.path.insert(0, str(PROJECT_ROOT))

from src.retriever import retrieve  # noqa: E402
from src.vectorstore import get_collection_count  # noqa: E402


def _doc_matches(source: str, expected_doc: str) -> bool:
    return expected_doc.lower() in source.lower()


def _page_in_range(page: int, page_min: int, page_max: int) -> bool:
    return page_min <= page <= page_max


def evaluate(top_k: int = 5, hybrid: bool = False) -> dict:
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Missing eval set: {EVAL_PATH}")

    questions = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    chunk_count = get_collection_count()
    if chunk_count == 0:
        return {
            "hit_rate": 0.0,
            "hits": 0,
            "total": len(questions),
            "chunk_count": 0,
            "mode": "hybrid" if hybrid else "dense",
            "error": "Vector store is empty. Run scripts/build_index.py first.",
            "results": [],
        }

    results = []
    hits = 0
    for item in questions:
        question = item["question"]
        expected_doc = item["expected_doc"]
        page_min = int(item.get("expected_page_min", 1))
        page_max = int(item.get("expected_page_max", 9999))

        retrieved = retrieve(question, top_k=top_k, hybrid=hybrid)
        matched = False
        matched_pages: list[int] = []
        for row in retrieved:
            if _doc_matches(row.source, expected_doc):
                matched_pages.append(row.page)
                if _page_in_range(row.page, page_min, page_max):
                    matched = True
                    break

        if matched:
            hits += 1

        results.append(
            {
                "id": item.get("id", ""),
                "question": question,
                "expected_doc": expected_doc,
                "hit": matched,
                "top_sources": [r.source for r in retrieved[:3]],
                "top_pages": [r.page for r in retrieved[:3]],
            }
        )

    hit_rate = hits / len(questions) if questions else 0.0
    return {
        "hit_rate": round(hit_rate, 4),
        "hits": hits,
        "total": len(questions),
        "chunk_count": chunk_count,
        "top_k": top_k,
        "mode": "hybrid" if hybrid else "dense",
        "results": results,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate retrieval hit rate.")
    parser.add_argument("--hybrid", action="store_true", help="Enable hybrid BM25 + dense search")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    args = parser.parse_args()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = evaluate(top_k=args.top_k, hybrid=args.hybrid)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    mode_str = "Hybrid (BM25 + Dense)" if args.hybrid else "Dense Vector"
    print(f"Retrieval evaluation ({mode_str}) — {report['hits']}/{report['total']} hits")
    print(f"Hit rate: {report['hit_rate'] * 100:.1f}%")
    print(f"Chunk count: {report['chunk_count']}")
    print(f"Report: {REPORT_PATH}")

    if report.get("error"):
        print(f"WARNING: {report['error']}")
        return 1
    if report["hit_rate"] < 0.70:
        print("WARNING: Hit rate below 70% target.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

