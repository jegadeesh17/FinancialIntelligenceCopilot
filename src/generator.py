"""OpenRouter-backed answer generation with citations."""

from __future__ import annotations

import httpx

from src.config import Settings, get_settings
from src.schemas import Citation, RAGResponse, RetrievalResult

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = httpx.Timeout(45.0, connect=15.0)
MAX_CONTEXT_CHUNKS = 5


def build_prompt(question: str, contexts: list[RetrievalResult]) -> str:
    """Build a grounded prompt from retrieved chunks and a user question."""
    context_lines = []
    for idx, item in enumerate(contexts[:MAX_CONTEXT_CHUNKS], start=1):
        context_lines.append(
            f"[{idx}] Source: {item.source}, Page: {item.page}\n{item.text}"
        )
    context_block = "\n\n".join(context_lines) if context_lines else "No context available."
    return (
        "You are a financial compliance assistant.\n"
        "Answer strictly using the provided context. If context is insufficient, "
        "say so explicitly.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Return a concise answer."
    )


def _call_openrouter(prompt: str, settings: Settings) -> str:
    if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("sk-or-v1-your"):
        raise ValueError("OPENROUTER_API_KEY is missing. Set it in .env before live generation.")

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": "You provide grounded answers from supplied context."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def _make_citations(contexts: list[RetrievalResult]) -> list[Citation]:
    seen: set[tuple[str, int]] = set()
    citations: list[Citation] = []
    for item in contexts[:MAX_CONTEXT_CHUNKS]:
        key = (item.source, item.page)
        if key in seen:
            continue
        seen.add(key)
        citations.append(Citation(source=item.source, page=item.page))
    return citations


def generate_answer(
    question: str,
    contexts: list[RetrievalResult],
    settings: Settings | None = None,
) -> RAGResponse:
    """Generate a grounded answer and attach source/page citations."""
    settings = settings or get_settings()
    if not question.strip():
        return RAGResponse(answer="Please provide a non-empty question.", citations=[], model=settings.openrouter_model)
    if not contexts:
        return RAGResponse(
            answer="I could not find relevant context in the document corpus.",
            citations=[],
            model=settings.openrouter_model,
        )

    prompt = build_prompt(question, contexts)
    answer = _call_openrouter(prompt, settings=settings)
    return RAGResponse(
        answer=answer,
        citations=_make_citations(contexts),
        model=settings.openrouter_model,
    )
