"""ChromaDB vector store for document chunk embeddings."""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import Settings, get_settings
from src.embeddings import embed_texts
from src.indexing import write_index_metadata
from src.ingest_docs import ingest_directory
from src.schemas import DocumentChunk

COLLECTION_NAME = "financial_compliance"
UPSERT_BATCH_SIZE = 500


def chunk_id(chunk: DocumentChunk) -> str:
    """Stable unique id for a chunk within the vector store."""
    return f"{chunk.source}::p{chunk.page}::c{chunk.chunk_index}"


def get_chroma_client(
    persist_dir: Path | None = None,
    settings: Settings | None = None,
) -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client."""
    settings = settings or get_settings()
    path = Path(persist_dir) if persist_dir else settings.chroma_path
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_or_create_collection(
    client: chromadb.ClientAPI,
    name: str = COLLECTION_NAME,
) -> Collection:
    return client.get_or_create_collection(name=name)


def upsert_chunks(
    chunks: list[DocumentChunk],
    client: chromadb.ClientAPI | None = None,
    collection_name: str = COLLECTION_NAME,
    settings: Settings | None = None,
) -> int:
    """Embed and upsert chunks into ChromaDB. Returns number of chunks stored."""
    if not chunks:
        return 0

    settings = settings or get_settings()
    client = client or get_chroma_client(settings=settings)
    collection = get_or_create_collection(client, name=collection_name)

    for i in range(0, len(chunks), UPSERT_BATCH_SIZE):
        batch = chunks[i : i + UPSERT_BATCH_SIZE]
        texts = [chunk.text for chunk in batch]
        embeddings = embed_texts(texts, settings=settings)
        ids = [chunk_id(chunk) for chunk in batch]
        metadatas = [
            {
                "source": chunk.source,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in batch
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
    return len(chunks)


def get_collection_count(
    client: chromadb.ClientAPI | None = None,
    collection_name: str = COLLECTION_NAME,
    settings: Settings | None = None,
) -> int:
    settings = settings or get_settings()
    client = client or get_chroma_client(settings=settings)
    collection = get_or_create_collection(client, name=collection_name)
    return collection.count()


def build_vector_index(
    pdf_dir: Path | None = None,
    settings: Settings | None = None,
    collection_name: str = COLLECTION_NAME,
) -> int:
    """Ingest PDFs from disk, embed chunks, and persist to ChromaDB."""
    settings = settings or get_settings()
    target_dir = pdf_dir or settings.raw_pdf_path
    chunks = ingest_directory(directory=target_dir, settings=settings)
    client = get_chroma_client(settings=settings)
    stored = upsert_chunks(
        chunks,
        client=client,
        collection_name=collection_name,
        settings=settings,
    )
    pdf_count = len(list(Path(target_dir).glob("*.pdf")))
    write_index_metadata(chunk_count=stored, pdf_count=pdf_count, settings=settings)
    return stored
