"""Helpers for Streamlit chat session state and citation formatting."""

from __future__ import annotations

import streamlit as st

from src.schemas import Citation

WELCOME_MESSAGE = (
    "Welcome to **Financial Intelligence Copilot**. "
    "Ask questions about RBI/SEBI regulations, listed company annual reports, "
    "IRDAI insurance circulars, or NISM research analyst material — "
    "every answer is grounded in your document library with page citations."
)


def init_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE, "citations": []}]


def append_message(role: str, content: str, citations: list[Citation] | list[dict] | None = None) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "citations": citations or [],
        }
    )


def format_citations(citations: list[Citation] | list[dict]) -> str:
    if not citations:
        return ""
    grouped: dict[str, set[int]] = {}
    for c in citations:
        source = c.source if hasattr(c, "source") else c.get("source", "")
        page = int(c.page if hasattr(c, "page") else c.get("page", 0))
        grouped.setdefault(source, set()).add(page)

    parts = []
    for source, pages in grouped.items():
        ordered = sorted(p for p in pages if p > 0)
        page_text = ", ".join(f"p.{p}" for p in ordered[:5])
        if len(ordered) > 5:
            page_text += ", ..."
        short = source if len(source) <= 42 else source[:39] + "..."
        parts.append(f"{short} ({page_text})")
    return " · ".join(parts)


def citations_html(citations: list[Citation] | list[dict]) -> str:
    """Backward-compatible alias for UI citation chips."""
    from src.ui_styles import citation_chips_html

    return citation_chips_html(citations)
