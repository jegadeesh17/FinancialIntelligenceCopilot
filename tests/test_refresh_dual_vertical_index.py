"""Tests for build_index corpus summary helpers."""

from __future__ import annotations

from src.corpus_stats import summarize_corpus


def test_summarize_corpus_counts_all_categories(tmp_path):
    raw = tmp_path / "raw_pdfs"
    raw.mkdir()
    files = [
        "rbi_master_direction_kyc.pdf",
        "sebi_circular_disclosure.pdf",
        "hdfc_bank_annual_report.pdf",
        "irdai_life_insurance_products.pdf",
        "nism_research_analyst_workbook.pdf",
    ]
    for name in files:
        (raw / name).write_bytes(b"%PDF")

    stats = summarize_corpus(raw)
    assert stats["total_pdfs"] == 5
    assert len(stats["category_counts"]) == 4
