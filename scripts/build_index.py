"""Build or rebuild the ChromaDB vector index from data/raw_pdfs/."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings  # noqa: E402
from src.vectorstore import build_vector_index, get_collection_count  # noqa: E402


def main() -> int:
    settings = get_settings()
    pdf_dir = settings.raw_pdf_path
    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}. Run: python scripts/download_docs.py")
        return 1

    print(f"Indexing {len(pdfs)} PDF(s) from {pdf_dir} ...")
    stored = build_vector_index(pdf_dir=pdf_dir, settings=settings)
    print(f"Stored {stored} chunks. Collection count: {get_collection_count(settings=settings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
