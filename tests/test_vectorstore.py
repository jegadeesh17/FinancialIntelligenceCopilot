"""
Embeddings & Vector Store tests.

Run: pytest tests/test_vectorstore.py -v
Integration (full corpus): pytest tests/test_vectorstore.py -m integration -v
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

    return Settings(chunk_size=200, chunk_overlap=40)


@pytest.fixture
def chroma_dir(tmp_path):
    return tmp_path / "chroma_test"


@pytest.fixture
def sample_chunks():
    from src.schemas import DocumentChunk

    return [
        DocumentChunk(
            source="rbi_master_direction_kyc.pdf",
            page=1,
            text="Banks shall obtain KYC documents for individual customers.",
            chunk_index=0,
        ),
        DocumentChunk(
            source="hdfc_bank_annual_report.pdf",
            page=42,
            text="Net interest income for the financial year increased year over year.",
            chunk_index=0,
        ),
        DocumentChunk(
            source="sebi_circular_disclosure.pdf",
            page=2,
            text="Listed entities must comply with LODR disclosure requirements.",
            chunk_index=0,
        ),
    ]


class TestEmbeddings:
    def test_embed_texts_returns_vectors(self, settings):
        from src.embeddings import EMBEDDING_DIMENSION, embed_texts

        vectors = embed_texts(
            ["KYC requirements for banks", "Net interest income disclosure"],
            settings=settings,
        )
        assert len(vectors) == 2
        assert len(vectors[0]) == EMBEDDING_DIMENSION
        assert len(vectors[1]) == EMBEDDING_DIMENSION

    def test_embed_query_returns_single_vector(self, settings):
        from src.embeddings import embed_query

        vector = embed_query("What is the minimum capital requirement?", settings=settings)
        assert isinstance(vector, list)
        assert len(vector) == 384

    def test_embed_empty_list_returns_empty(self, settings):
        from src.embeddings import embed_texts

        assert embed_texts([], settings=settings) == []


class TestVectorStore:
    def test_upsert_chunks_persists(self, sample_chunks, chroma_dir, settings):
        from src.vectorstore import get_chroma_client, get_collection_count, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        stored = upsert_chunks(sample_chunks, client=client, settings=settings)
        assert stored == 3
        assert get_collection_count(client=client) == 3

    def test_collection_count_matches_chunks(self, sample_chunks, chroma_dir, settings):
        from src.vectorstore import get_chroma_client, get_collection_count, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)
        assert get_collection_count(client=client) == len(sample_chunks)

    def test_persistence_survives_client_restart(self, sample_chunks, chroma_dir, settings):
        from src.vectorstore import get_chroma_client, get_collection_count, upsert_chunks

        client1 = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client1, settings=settings)

        client2 = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        assert get_collection_count(client=client2) == len(sample_chunks)

    def test_upsert_is_idempotent_for_same_ids(self, sample_chunks, chroma_dir, settings):
        from src.vectorstore import get_chroma_client, get_collection_count, upsert_chunks

        client = get_chroma_client(persist_dir=chroma_dir, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)
        upsert_chunks(sample_chunks, client=client, settings=settings)
        assert get_collection_count(client=client) == len(sample_chunks)

    def test_chunk_id_is_unique_per_chunk(self, sample_chunks):
        from src.vectorstore import chunk_id

        ids = [chunk_id(c) for c in sample_chunks]
        assert len(ids) == len(set(ids))


@pytest.mark.integration
class TestBuildVectorIndex:
    def test_build_index_from_real_pdfs_if_present(self, chroma_dir, settings):
        from src.config import get_settings
        from src.ingest_docs import ingest_directory
        from src.vectorstore import build_vector_index, get_chroma_client, get_collection_count

        pdf_dir = get_settings().raw_pdf_path
        if not list(pdf_dir.glob("*.pdf")):
            pytest.skip("No PDFs in data/raw_pdfs/")

        settings = settings.model_copy(update={"chroma_persist_dir": str(chroma_dir)})
        expected = len(ingest_directory(pdf_dir, settings=settings))
        stored = build_vector_index(pdf_dir=pdf_dir, settings=settings)
        assert stored == expected
        assert get_collection_count(
            client=get_chroma_client(persist_dir=chroma_dir, settings=settings),
        ) == expected
