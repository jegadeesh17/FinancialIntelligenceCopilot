"""Tests for corpus category summary utilities."""

from __future__ import annotations

from src.corpus_stats import classify_document_category, list_pdfs_by_category, summarize_corpus


def test_classify_document_category():
    assert classify_document_category("rbi_master_direction_kyc.pdf") == "regulatory"
    assert classify_document_category("sebi_circular_disclosure.pdf") == "regulatory"
    assert classify_document_category("irdai_life_insurance_products.pdf") == "insurance"
    assert classify_document_category("nism_research_analyst_workbook.pdf") == "exam_reference"
    assert classify_document_category("hdfc_bank_annual_report.pdf") == "annual_report"


def test_summarize_corpus_by_category(tmp_path):
    raw = tmp_path / "raw_pdfs"
    raw.mkdir()
    (raw / "rbi_master_direction_kyc.pdf").write_bytes(b"%PDF-1.4 compliance")
    (raw / "hdfc_bank_annual_report.pdf").write_bytes(b"%PDF-1.4 annual")
    (raw / "irdai_life_insurance_products.pdf").write_bytes(b"%PDF-1.4 insurance")
    (raw / "nism_research_analyst_workbook.pdf").write_bytes(b"%PDF-1.4 exam")

    stats = summarize_corpus(raw)
    assert stats["total_pdfs"] == 4
    assert stats["category_counts"]["regulatory"] == 1
    assert stats["category_counts"]["annual_report"] == 1
    assert stats["category_counts"]["insurance"] == 1
    assert stats["category_counts"]["exam_reference"] == 1
    assert stats["regulator_counts"]["RBI"] == 1
    assert stats["regulator_counts"]["IRDAI"] == 1


def test_list_pdfs_by_category(tmp_path):
    raw = tmp_path / "raw_pdfs"
    raw.mkdir()
    (raw / "sebi_circular_disclosure.pdf").write_bytes(b"%PDF")
    (raw / "tcs_annual_report.pdf").write_bytes(b"%PDF")

    grouped = list_pdfs_by_category(raw)
    assert grouped["regulatory"] == ["sebi_circular_disclosure.pdf"]
    assert grouped["annual_report"] == ["tcs_annual_report.pdf"]
