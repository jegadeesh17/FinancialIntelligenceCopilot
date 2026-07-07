"""FastAPI service for Financial Compliance RAG."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.generator import generate_answer
from src.indexing import read_index_metadata
from src.retriever import retrieve
from src.vectorstore import get_collection_count

app = FastAPI(
    title="Financial Compliance RAG API",
    description="Citation-grounded compliance Q&A over regulatory PDF corpus.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class CitationOut(BaseModel):
    source: str
    page: int


class SourceChunkOut(BaseModel):
    source: str
    page: int
    text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    model: str
    source_chunks: list[SourceChunkOut]


@app.get("/health")
def health() -> dict:
    meta = read_index_metadata()
    return {
        "status": "ok",
        "chunk_count": get_collection_count(),
        "index_metadata": meta,
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")

    contexts = retrieve(question)
    response = generate_answer(question, contexts)

    return AskResponse(
        answer=response.answer,
        citations=[CitationOut(source=c.source, page=c.page) for c in response.citations],
        model=response.model,
        source_chunks=[
            SourceChunkOut(
                source=item.source,
                page=item.page,
                text=item.text[:500],
                score=item.score,
            )
            for item in contexts[:5]
        ],
    )
