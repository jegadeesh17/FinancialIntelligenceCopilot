"""
Phase 4 checkpoint tests — Retrieval System.

Run: pytest tests/test_phase4_retriever.py -v
Integration: pytest tests/test_phase4_retriever.py -m integration -v
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def settings():
    sys.path.insert(0, str(PROJECT_ROOT))
    if "src.config" in sys.modules:
        importlib.reload(sys.modules["src.config"])
    from src.config import Settings

    return Settings(chunk_size=200, chunk_overlap=40, top_k=2)


@pytest.fixture
def chroma_dir(tmp_path):
    return tmp_path / "chroma_retrieval_test"


@pytest.fixture
def sample_chunks():
    from src.schemas import DocumentChunk

    return [
        DocumentChunk(
            source="rbi_master_direction_kyc.pdf",
            page=12,
            chunk_index=0,
            text="Banks shall collect proof of identity and proof of address under KYC norms.",
        ),
        DocumentChunk(
            source="hdfc_bank_annual_report.pdf",
            page=50,
            chunk_index=0,
            text="Net interest income increased for the year and total deposits rose substantially.",
        ),
        DocumentChunk(
            source="sebi_circular_disclosure.pdf",
            page=2,
            chunk_index=0,
            text="Listed entities must comply with disclosure obligations under SEBI LODR regulations.",
        ),
    ]


class TestRetriever:
    def test_retrieve_returns_top_k(self, sample_chunks, chroma_dir, settings):
        from src.retriever import retrieve
        from src.vectorstore import get_chroma_client, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)

        results = retrieve(
            "What are KYC requirements for customers?",
            top_k=2,
            settings=settings,
            persist_dir=chroma_dir,
        )
        assert len(results) == 2

    def test_retrieve_preserves_metadata(self, sample_chunks, chroma_dir, settings):
        from src.retriever import retrieve
        from src.vectorstore import get_chroma_client, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)

        results = retrieve(
            "What does SEBI say about disclosure obligations?",
            top_k=1,
            settings=settings,
            persist_dir=chroma_dir,
        )
        assert len(results) == 1
        result = results[0]
        assert result.source.endswith(".pdf")
        assert result.page >= 1
        assert result.text.strip()
        assert isinstance(result.score, float)

    def test_empty_query_returns_empty(self, sample_chunks, chroma_dir, settings):
        from src.retriever import retrieve
        from src.vectorstore import get_chroma_client, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)
        assert retrieve("   ", settings=settings, persist_dir=chroma_dir) == []

    def test_retrieve_empty_collection_returns_empty(self, chroma_dir, settings):
        from src.retriever import retrieve
        from src.vectorstore import get_chroma_client, get_or_create_collection

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        get_or_create_collection(client)
        results = retrieve("Any query", settings=settings, persist_dir=chroma_dir)
        assert results == []


@pytest.mark.integration
class TestRetrieverIntegration:
    def test_retrieve_from_real_corpus_if_present(self, settings, tmp_path):
        from src.config import get_settings
        from src.retriever import retrieve
        from src.vectorstore import build_vector_index

        pdf_dir = get_settings().raw_pdf_path
        if not list(pdf_dir.glob("*.pdf")):
            pytest.skip("No PDFs in data/raw_pdfs/")

        persist_dir = tmp_path / "phase4_real_chroma"
        runtime_settings = settings.model_copy(update={"chroma_persist_dir": str(persist_dir)})
        stored = build_vector_index(pdf_dir=pdf_dir, settings=runtime_settings)
        assert stored > 0

        results = retrieve(
            "What KYC documents are required?",
            settings=runtime_settings,
            persist_dir=persist_dir,
            top_k=3,
        )
        assert len(results) > 0
