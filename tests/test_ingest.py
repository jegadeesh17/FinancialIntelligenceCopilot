"""
Document Ingestion tests.

Run: pytest tests/test_ingest.py -v
Integration (real PDFs): pytest tests/test_ingest.py -m integration -v
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory) -> Path:
    sys.path.insert(0, str(PROJECT_ROOT))
    from tests.fixtures.make_sample_pdf import write_sample_pdf

    pdf_dir = tmp_path_factory.mktemp("pdfs")
    return write_sample_pdf(pdf_dir / "sample_compliance.pdf")


@pytest.fixture(scope="module")
def settings():
    sys.path.insert(0, str(PROJECT_ROOT))
    if "src.config" in sys.modules:
        importlib.reload(sys.modules["src.config"])
    from src.config import Settings

    return Settings(chunk_size=200, chunk_overlap=40)


class TestChunking:
    def test_chunk_page_text_respects_paragraph_boundaries(self):
        from src.ingest_docs import chunk_page_text

        text = "Paragraph one about KYC requirements.\n\nParagraph two about capital adequacy."
        chunks = chunk_page_text(text, chunk_size=120, chunk_overlap=20)
        assert len(chunks) >= 1
        assert "KYC" in chunks[0]

    def test_chunk_page_text_splits_long_paragraph(self):
        from src.ingest_docs import chunk_page_text

        text = "A" * 500
        chunks = chunk_page_text(text, chunk_size=200, chunk_overlap=40)
        assert len(chunks) >= 2
        assert all(len(c) <= 200 for c in chunks)

    def test_empty_text_returns_no_chunks(self):
        from src.ingest_docs import chunk_page_text

        assert chunk_page_text("   \n\n  ", chunk_size=200, chunk_overlap=20) == []


class TestPdfExtraction:
    def test_extract_pages_from_sample_pdf(self, sample_pdf: Path):
        from src.ingest_docs import extract_pages

        pages = extract_pages(sample_pdf)
        assert len(pages) == 3
        assert pages[0][0] == 1
        assert "KYC" in pages[0][1]

    def test_extract_pages_missing_file_raises(self):
        from src.ingest_docs import extract_pages

        with pytest.raises(FileNotFoundError):
            extract_pages(PROJECT_ROOT / "data" / "raw_pdfs" / "nonexistent.pdf")


class TestIngestPdf:
    def test_ingest_pdf_returns_chunks_with_metadata(self, sample_pdf: Path, settings):
        from src.ingest_docs import ingest_pdf

        chunks = ingest_pdf(sample_pdf, settings=settings)
        assert len(chunks) >= 3
        first = chunks[0]
        assert first.source == "sample_compliance.pdf"
        assert first.page >= 1
        assert len(first.text) > 0
        assert first.chunk_index == 0

    def test_all_chunks_have_required_fields(self, sample_pdf: Path, settings):
        from src.ingest_docs import ingest_pdf

        for chunk in ingest_pdf(sample_pdf, settings=settings):
            assert chunk.source
            assert chunk.page >= 1
            assert chunk.text.strip()
            assert chunk.chunk_index >= 0


class TestIngestDirectory:
    def test_ingest_directory_loads_all_pdfs(self, sample_pdf: Path, settings, tmp_path):
        from src.ingest_docs import ingest_directory

        pdf_dir = tmp_path / "corpus"
        pdf_dir.mkdir()
        (pdf_dir / "doc_a.pdf").write_bytes(sample_pdf.read_bytes())
        (pdf_dir / "doc_b.pdf").write_bytes(sample_pdf.read_bytes())

        chunks = ingest_directory(pdf_dir, settings=settings)
        sources = {c.source for c in chunks}
        assert sources == {"doc_a.pdf", "doc_b.pdf"}
        assert len(chunks) >= 6

    def test_ingest_directory_missing_raises(self, settings):
        from src.ingest_docs import ingest_directory

        with pytest.raises(FileNotFoundError):
            ingest_directory(PROJECT_ROOT / "data" / "no_such_dir", settings=settings)


@pytest.mark.integration
class TestRealPdfCorpus:
    """Requires PDFs in data/raw_pdfs/ (run scripts/download_docs.py first)."""

    def test_ingest_real_corpus_if_present(self, settings):
        from src.config import get_settings
        from src.ingest_docs import ingest_directory

        pdf_dir = get_settings().raw_pdf_path
        pdfs = list(pdf_dir.glob("*.pdf"))
        if not pdfs:
            pytest.skip("No PDFs in data/raw_pdfs/ — run scripts/download_docs.py or add manually")

        chunks = ingest_directory(pdf_dir, settings=settings)
        assert len(chunks) >= 1
        assert all(c.source.endswith(".pdf") for c in chunks)
