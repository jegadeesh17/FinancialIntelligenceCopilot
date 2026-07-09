"""FastAPI service for Financial Intelligence Copilot."""

from __future__ import annotations

from collections import defaultdict, deque
from time import time

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from src.config import get_settings
from src.corpus_stats import summarize_corpus
from src.generator import generate_answer
from src.indexing import read_index_metadata
from src.retriever import get_best_score, is_low_confidence, retrieve
from src.vectorstore import get_collection_count

app = FastAPI(
    title="Financial Intelligence Copilot API",
    description="Citation-grounded Q&A over regulatory, annual report, insurance, and exam PDF corpus.",
    version="1.0.0",
)
_REQUEST_WINDOW_SECONDS = 60
_request_buckets: dict[str, deque[float]] = defaultdict(deque)


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
    retrieved_at: str = ""
    regulator: str = "other"
    document_category: str = "annual_report"


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    model: str
    low_confidence: bool
    best_score: float | None = None
    source_chunks: list[SourceChunkOut]


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    corpus = summarize_corpus(settings.raw_pdf_path)
    meta = read_index_metadata()
    return {
        "status": "ok",
        "chunk_count": get_collection_count(),
        "corpus": corpus,
        "index_metadata": meta,
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request, x_api_key: str | None = Header(default=None)) -> AskResponse:
    settings = get_settings()
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    client_ip = request.client.host if request.client else "unknown"
    now = time()
    bucket = _request_buckets[client_ip]
    while bucket and now - bucket[0] > _REQUEST_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= settings.api_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    bucket.append(now)

    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")

    contexts = retrieve(question)
    response = generate_answer(question, contexts)
    low_confidence = is_low_confidence(contexts)
    best_score = get_best_score(contexts)

    return AskResponse(
        answer=response.answer,
        citations=[CitationOut(source=c.source, page=c.page) for c in response.citations],
        model=response.model,
        low_confidence=low_confidence,
        best_score=best_score,
        source_chunks=[
            SourceChunkOut(
                source=item.source,
                page=item.page,
                text=item.text[:500],
                score=item.score,
                retrieved_at=item.retrieved_at,
                regulator=item.regulator,
                document_category=item.document_category,
            )
            for item in contexts[:5]
        ],
    )
