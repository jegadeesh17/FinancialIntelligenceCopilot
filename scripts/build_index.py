"""Build or rebuild the ChromaDB vector index from data/raw_pdfs/."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings  # noqa: E402
from src.corpus_stats import summarize_corpus  # noqa: E402
from src.vectorstore import build_vector_index, get_collection_count  # noqa: E402


def main() -> int:
    settings = get_settings()
    pdf_dir = settings.raw_pdf_path
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}. Add real PDFs manually — see docs/DATA_SOURCES.md")
        return 1

    stats = summarize_corpus(pdf_dir)
    print(f"Indexing {stats['total_pdfs']} PDF(s) from {pdf_dir}")
    for category, count in stats.get("category_counts", {}).items():
        share = stats.get("category_shares", {}).get(category, 0.0)
        print(f"  {category}: {count} ({share:.0%})")

    print("\nRebuilding vector index ...")
    stored = build_vector_index(pdf_dir=pdf_dir, settings=settings)
    print(f"Stored chunks: {stored}")
    print(f"Collection count: {get_collection_count(settings=settings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
