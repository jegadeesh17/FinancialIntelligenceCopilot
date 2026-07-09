"""Corpus-level summary utilities by document category."""

from __future__ import annotations

from pathlib import Path

DOCUMENT_CATEGORIES = ("regulatory", "annual_report", "insurance", "exam_reference")


def classify_document_category(filename: str) -> str:
    """Classify a PDF filename into a document category."""
    low = filename.lower()
    if low.startswith("rbi_") or low.startswith("sebi_"):
        return "regulatory"
    if low.startswith("irdai_"):
        return "insurance"
    if low.startswith("nism_"):
        return "exam_reference"
    return "annual_report"


def infer_regulator(filename: str, category: str) -> str:
    low = filename.lower()
    if category == "regulatory":
        if "rbi" in low:
            return "RBI"
        if "sebi" in low:
            return "SEBI"
    if category == "insurance":
        return "IRDAI"
    return "other"


def summarize_corpus(raw_pdf_dir: Path) -> dict:
    """Return corpus stats grouped by document category."""
    pdfs = sorted(raw_pdf_dir.glob("*.pdf"))
    category_counts: dict[str, int] = {c: 0 for c in DOCUMENT_CATEGORIES}
    regulator_counts: dict[str, int] = {}

    for pdf in pdfs:
        category = classify_document_category(pdf.name)
        category_counts[category] = category_counts.get(category, 0) + 1
        regulator = infer_regulator(pdf.name, category)
        if regulator != "other":
            regulator_counts[regulator] = regulator_counts.get(regulator, 0) + 1

    total = len(pdfs)
    shares = {
        k: round(v / total, 3) if total else 0.0
        for k, v in category_counts.items()
        if v > 0
    }
    return {
        "total_pdfs": total,
        "category_counts": {k: v for k, v in category_counts.items() if v > 0},
        "category_shares": shares,
        "regulator_counts": regulator_counts,
    }


def list_pdfs_by_category(raw_pdf_dir: Path) -> dict[str, list[str]]:
    """Return filenames grouped by document category."""
    grouped: dict[str, list[str]] = {c: [] for c in DOCUMENT_CATEGORIES}
    for pdf in sorted(raw_pdf_dir.glob("*.pdf")):
        grouped[classify_document_category(pdf.name)].append(pdf.name)
    return {k: v for k, v in grouped.items() if v}
