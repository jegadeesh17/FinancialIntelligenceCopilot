"""Pydantic models for document ingestion and RAG pipeline."""

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A text chunk extracted from a PDF with source metadata."""

    source: str = Field(..., min_length=1, description="PDF filename")
    page: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(..., min_length=1, description="Chunk text content")
    chunk_index: int = Field(
        default=0,
        ge=0,
        description="0-based chunk index within the source document",
    )


class RetrievalResult(BaseModel):
    """Single retrieved chunk and its similarity score."""

    source: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    chunk_index: int = Field(default=0, ge=0)
    score: float = Field(..., description="Distance score from vector search")


class Citation(BaseModel):
    """Citation entry for grounded responses."""

    source: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)


class RAGResponse(BaseModel):
    """Final generated answer with supporting citations."""

    answer: str = Field(..., min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    model: str = Field(default="")
