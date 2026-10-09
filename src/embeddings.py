"""ONNX all-MiniLM-L6-v2 embeddings for document chunks (no torch required)."""

from __future__ import annotations

from functools import lru_cache

from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

from src.config import Settings

# all-MiniLM-L6-v2 output dimension
EMBEDDING_DIMENSION = 384


@lru_cache
def get_embedding_function() -> ONNXMiniLM_L6_V2:
    """Load and cache the ONNX embedding model (downloads to ~/.cache/chroma on first use)."""
    return ONNXMiniLM_L6_V2()


def embed_texts(
    texts: list[str],
    settings: Settings | None = None,
) -> list[list[float]]:
    """Convert text strings to embedding vectors."""
    if not texts:
        return []

    vectors = get_embedding_function()(texts)
    return [vector.tolist() for vector in vectors]


def embed_query(
    query: str,
    settings: Settings | None = None,
) -> list[float]:
    """Embed a single user query."""
    return embed_texts([query], settings=settings)[0]
