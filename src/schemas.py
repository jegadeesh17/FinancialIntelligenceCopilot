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
    retrieved_at: str = Field(default="", description="Ingestion timestamp (ISO)")
    regulator: str = Field(default="other", description="Regulator tag: RBI, SEBI, IRDAI, or other")
    document_category: str = Field(
        default="annual_report",
        description="Document category: regulatory, annual_report, insurance, exam_reference",
    )


class RetrievalResult(BaseModel):
    """Single retrieved chunk and its similarity score."""

    source: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    chunk_index: int = Field(default=0, ge=0)
    score: float = Field(..., description="Distance score from vector search")
    retrieved_at: str = Field(default="")
    regulator: str = Field(default="other")
    document_category: str = Field(default="annual_report")


class Citation(BaseModel):
    """Citation entry for grounded responses."""

    source: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)


class RAGResponse(BaseModel):
    """Final generated answer with supporting citations."""

    answer: str = Field(..., min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    model: str = Field(default="")
    low_confidence: bool = Field(default=False)
    best_score: float | None = Field(default=None, description="Best (lowest) retrieval distance.")
