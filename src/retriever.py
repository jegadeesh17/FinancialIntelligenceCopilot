"""Top-k semantic retrieval from ChromaDB."""

from __future__ import annotations

from pathlib import Path

from src.config import Settings, get_settings
from src.embeddings import embed_query
from src.schemas import RetrievalResult
from src.vectorstore import COLLECTION_NAME, get_chroma_client, get_or_create_collection


def retrieve(
    query: str,
    top_k: int | None = None,
    max_distance: float | None = None,
    settings: Settings | None = None,
    persist_dir: Path | None = None,
    collection_name: str = COLLECTION_NAME,
) -> list[RetrievalResult]:
    """Return top-k semantically similar chunks with metadata."""
    if not query.strip():
        return []

    settings = settings or get_settings()
    n_results = top_k or settings.top_k

    client = get_chroma_client(persist_dir=persist_dir, settings=settings)
    collection = get_or_create_collection(client, name=collection_name)
    if collection.count() == 0:
        return []

    query_vector = embed_query(query, settings=settings)
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    results: list[RetrievalResult] = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        if max_distance is not None and float(distance) > max_distance:
            continue
        md = metadata or {}
        results.append(
            RetrievalResult(
                source=str(md.get("source", "")),
                page=int(md.get("page", 1)),
                chunk_index=int(md.get("chunk_index", 0)),
                text=text,
                score=float(distance),
            )
        )
    return results
