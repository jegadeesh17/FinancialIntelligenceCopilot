"""Top-k semantic retrieval from ChromaDB."""

from __future__ import annotations

from pathlib import Path

from src.config import Settings, get_settings
from src.embeddings import embed_query
from src.schemas import RetrievalResult
from src.vectorstore import COLLECTION_NAME, get_chroma_client, get_or_create_collection


def _compute_rrf_indices(
    query: str,
    documents: list[str],
    alpha: float = 0.5,
    rrf_k: float = 60.0,
) -> list[int]:
    """Compute Reciprocal Rank Fusion (RRF) indices combining dense rank and BM25 rank."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        return list(range(len(documents)))

    tokenized_corpus = [doc.lower().split() for doc in documents]
    tokenized_query = query.lower().split()
    if not tokenized_query or not tokenized_corpus:
        return list(range(len(documents)))

    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenized_query)

    # BM25 rank (higher score = lower rank index)
    bm25_order = sorted(range(len(documents)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_rank = {idx: rank for rank, idx in enumerate(bm25_order)}

    # Dense rank (already sorted ascending by distance)
    dense_rank = {idx: idx for idx in range(len(documents))}

    # Weighted Reciprocal Rank Fusion
    rrf_scores = {}
    for idx in range(len(documents)):
        score_dense = 1.0 / (rrf_k + dense_rank[idx])
        score_bm25 = 1.0 / (rrf_k + bm25_rank[idx])
        rrf_scores[idx] = (1.0 - alpha) * score_dense + alpha * score_bm25

    return sorted(range(len(documents)), key=lambda idx: rrf_scores[idx], reverse=True)


def retrieve(
    query: str,
    top_k: int | None = None,
    max_distance: float | None = None,
    settings: Settings | None = None,
    persist_dir: Path | None = None,
    collection_name: str = COLLECTION_NAME,
    hybrid: bool = False,
    alpha: float = 0.5,
) -> list[RetrievalResult]:
    """Return top-k semantically similar chunks with metadata, optionally using hybrid BM25 fusion."""
    if not query.strip():
        return []

    settings = settings or get_settings()
    n_results = top_k or settings.top_k

    client = get_chroma_client(persist_dir=persist_dir, settings=settings)
    collection = get_or_create_collection(client, name=collection_name)
    count = collection.count()
    if count == 0:
        return []

    # Fetch larger candidate pool if running hybrid fusion
    query_k = min(count, max(n_results * 3, 15)) if hybrid else min(count, n_results)

    query_vector = embed_query(query, settings=settings)
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=query_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    # If hybrid re-ranking requested, compute RRF ordering
    if hybrid and len(documents) > 1:
        reranked_indices = _compute_rrf_indices(query, documents, alpha=alpha)
        documents = [documents[i] for i in reranked_indices]
        metadatas = [metadatas[i] for i in reranked_indices]
        distances = [distances[i] for i in reranked_indices]

    results: list[RetrievalResult] = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        if max_distance is not None and float(distance) > max_distance:
            continue
        md = metadata or {}
        category = md.get("document_category") or md.get("document_vertical", "annual_report")
        if category == "compliance":
            category = "annual_report"
        results.append(
            RetrievalResult(
                source=str(md.get("source", "")),
                page=int(md.get("page", 1)),
                chunk_index=int(md.get("chunk_index", 0)),
                text=text,
                score=float(distance),
                retrieved_at=str(md.get("retrieved_at", "")),
                regulator=str(md.get("regulator", "other")),
                document_category=str(category),
            )
        )
        if len(results) >= n_results:
            break

    return results


def retrieve_hybrid(
    query: str,
    top_k: int | None = None,
    alpha: float = 0.5,
    **kwargs,
) -> list[RetrievalResult]:
    """Convenience helper for hybrid retrieval combining BM25 keyword matching with dense embeddings."""
    return retrieve(query, top_k=top_k, hybrid=True, alpha=alpha, **kwargs)


def get_best_score(results: list[RetrievalResult]) -> float | None:
    """Return lowest distance score from retrieval results."""
    if not results:
        return None
    return min(item.score for item in results)


def is_low_confidence(
    results: list[RetrievalResult],
    settings: Settings | None = None,
    threshold: float | None = None,
) -> bool:
    """Decide if retrieval quality is too weak for confident answering."""
    if not results:
        return True
    settings = settings or get_settings()
    cut_off = threshold if threshold is not None else settings.low_confidence_distance
    best = get_best_score(results)
    if best is None:
        return True
    return best > cut_off
