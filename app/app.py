"""Financial Intelligence Copilot — product Streamlit UI."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _extract_index_if_needed():
    import zipfile
    db_dir = PROJECT_ROOT / "data" / "chroma_db"
    db_file = db_dir / "chroma.sqlite3"
    zip_path = PROJECT_ROOT / "data" / "chroma_db_lzma.zip"
    
    if zip_path.exists():
        if not db_file.exists() or db_file.stat().st_size < 1024 * 1024:
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(db_dir)
            except Exception as e:
                print(f"Extraction failed: {e}")

_extract_index_if_needed()


def _load_ui_styles():
    """Load UI constants from disk (avoids Streamlit stale import cache)."""
    import importlib.util

    path = PROJECT_ROOT / "src" / "ui_styles.py"
    spec = importlib.util.spec_from_file_location("fic_ui_styles", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load UI styles from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ui = _load_ui_styles()
PRODUCT_CSS = _ui.PRODUCT_CSS
CATEGORY_LABELS = _ui.CATEGORY_LABELS
SAMPLE_QUERIES = _ui.SAMPLE_QUERIES
citation_chips_html = _ui.citation_chips_html

from src.chat import append_message, init_chat_state  # noqa: E402
from src.corpus_stats import classify_document_category, list_pdfs_by_category, summarize_corpus  # noqa: E402
from src.generator import generate_answer  # noqa: E402
from src.indexing import read_index_metadata  # noqa: E402
from src.retriever import get_best_score, is_low_confidence, retrieve  # noqa: E402
from src.telemetry import log_query  # noqa: E402
from src.vectorstore import build_vector_index, get_chroma_client, get_collection_count, get_or_create_collection  # noqa: E402

RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"

st.set_page_config(
    page_title="Financial Intelligence Copilot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _format_index_time(iso_value: str | None) -> str:
    if not iso_value or iso_value == "unknown":
        return "Not indexed yet"
    try:
        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return iso_value


def _confidence_html(low_confidence: bool) -> str:
    if low_confidence:
        return '<span class="fic-badge-low">Low confidence — verify sources</span>'
    return '<span class="fic-badge-ok">Grounded answer</span>'


def _render_hero(total_pdfs: int, vector_count: int, category_counts: dict) -> None:
    pills = [
        f"{total_pdfs} documents",
        f"{vector_count:,} indexed chunks" if vector_count else "Index pending",
    ]
    for key in ("regulatory", "annual_report", "insurance", "exam_reference"):
        if category_counts.get(key):
            pills.append(f"{category_counts[key]} {CATEGORY_LABELS.get(key, key).lower()}")

    pill_html = "".join(f'<span class="fic-pill">{p}</span>' for p in pills)
    st.markdown(
        f"""
        <div class="fic-hero">
            <h1>Financial Intelligence Copilot</h1>
            <p>Ask natural-language questions across regulations, annual reports, insurance circulars,
            and exam reference material — with page-level citations from your private document library.</p>
            <div class="fic-pill-row">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _indexed_chunk_counts() -> dict[str, int]:
    collection = get_or_create_collection(get_chroma_client())
    rows = collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for md in rows.get("metadatas", []):
        if not md:
            continue
        source = str(md.get("source", ""))
        counts[source] = counts.get(source, 0) + 1
    return counts


def _render_knowledge_base() -> None:
    counts = _indexed_chunk_counts()
    by_category = list_pdfs_by_category(RAW_PDF_DIR, indexed_sources=list(counts.keys()))

    if not by_category:
        st.info("Your knowledge base is empty. Add PDFs to `data/raw_pdfs/` and rebuild the index.")
        return

    for category, names in by_category.items():
        label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())
        rows_html = []
        for name in names:
            pdf_path = RAW_PDF_DIR / name
            chunk_count = counts.get(name, 0)
            if pdf_path.exists():
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "Pre-indexed"
            status = "Indexed" if chunk_count else "Pending"
            rows_html.append(
                f"""
                <div class="fic-doc-row">
                    <div class="fic-doc-name">{name}</div>
                    <div class="fic-doc-meta">{size_str} · {chunk_count} chunks · {status}</div>
                </div>
                """
            )
        st.markdown(
            f"""
            <div class="fic-card fic-category-{category}" style="margin-bottom:1rem;">
                <div class="fic-section-label">{label} ({len(names)})</div>
                {''.join(rows_html)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _run_query(prompt: str, top_k: int, max_distance: float) -> None:
    append_message("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching your documents and drafting an answer..."):
            start = time.perf_counter()
            try:
                contexts = retrieve(prompt, top_k=top_k, max_distance=max_distance)
                response = generate_answer(prompt, contexts)
                low_confidence = is_low_confidence(contexts)
                best_score = get_best_score(contexts)

                st.markdown(_confidence_html(low_confidence), unsafe_allow_html=True)
                st.markdown(response.answer)

                if low_confidence:
                    suffix = f" Best match distance: {best_score:.3f}." if best_score is not None else ""
                    st.caption(f"We found limited supporting evidence.{suffix}")

                if response.citations:
                    st.markdown(
                        f'<div style="margin-top:0.75rem;">{citation_chips_html(response.citations)}</div>',
                        unsafe_allow_html=True,
                    )

                append_message("assistant", response.answer, response.citations)
                st.session_state.messages[-1]["contexts"] = [
                    {
                        "source": c.source,
                        "page": c.page,
                        "score": c.score,
                        "text": c.text,
                        "document_category": c.document_category,
                    }
                    for c in contexts
                ]
                st.session_state.messages[-1]["low_confidence"] = low_confidence
                st.session_state.messages[-1]["best_score"] = best_score

                latency_ms = (time.perf_counter() - start) * 1000
                top_sources = [c.source for c in contexts[:top_k]]
                fallback_used = (
                    len(contexts) == 0
                    or "could not find relevant context" in response.answer.lower()
                    or low_confidence
                )
                log_query(prompt, top_sources=top_sources, fallback_used=fallback_used, latency_ms=latency_ms)
            except Exception as exc:  # pragma: no cover
                st.error(f"Something went wrong: {exc}")
                append_message("assistant", f"Error: {exc}", [])


# --- Page bootstrap ---
st.markdown(PRODUCT_CSS, unsafe_allow_html=True)

try:
    vector_count = get_collection_count()
    indexed_counts = _indexed_chunk_counts()
except Exception:
    vector_count = 0
    indexed_counts = {}
corpus_stats = summarize_corpus(RAW_PDF_DIR, indexed_sources=list(indexed_counts.keys()))
meta = read_index_metadata()

init_chat_state()
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Defaults for retrieval settings (sidebar may override)
top_k = 5
max_distance = 1.2
show_debug = False

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Copilot")
    st.caption("Private RAG workspace for finance research and compliance.")

    st.markdown('<p class="fic-section-label">Library status</p>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="fic-card-muted">
            <div style="font-size:0.85rem;color:#0f172a;font-weight:600;">
                {corpus_stats.get('total_pdfs', 0)} source documents
            </div>
            <div style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;">
                {vector_count:,} chunks indexed
            </div>
            <div style="font-size:0.78rem;color:#64748b;margin-top:0.15rem;">
                Last rebuild: {_format_index_time(meta.get('last_indexed_at'))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if vector_count == 0:
        st.warning("Index not built yet. Open **Settings** below to rebuild.")

    with st.expander("Settings", expanded=False):
        top_k = st.slider("Sources per answer", min_value=1, max_value=10, value=5, step=1)
        max_distance = st.slider("Relevance threshold", min_value=0.0, max_value=2.0, value=1.2, step=0.05)
        show_debug = st.toggle("Show source excerpts", value=False)
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()

    with st.expander("Admin", expanded=False):
        st.caption("Rebuild after adding or replacing PDFs in `data/raw_pdfs/`.")
        if st.button("Rebuild document index", use_container_width=True):
            with st.spinner("Indexing documents..."):
                stored = build_vector_index()
            st.success(f"Indexed {stored:,} chunks.")
            st.rerun()

# --- Main content ---
_render_hero(
    total_pdfs=corpus_stats.get("total_pdfs", 0),
    vector_count=vector_count,
    category_counts=corpus_stats.get("category_counts", {}),
)

tab_copilot, tab_library = st.tabs(["Ask Copilot", "Knowledge base"])

with tab_copilot:
    st.markdown('<p class="fic-section-label">Suggested questions</p>', unsafe_allow_html=True)
    prompt_cols = st.columns(4)
    for col, (key, item) in zip(prompt_cols, SAMPLE_QUERIES.items()):
        with col:
            if st.button(item["label"], use_container_width=True, key=f"sample_{key}"):
                st.session_state.pending_prompt = item["query"]

    st.markdown("")

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant" and "low_confidence" in msg:
                    st.markdown(_confidence_html(bool(msg.get("low_confidence"))), unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("citations"):
                    st.markdown(
                        f'<div style="margin-top:0.5rem;">{citation_chips_html(msg.get("citations", []))}</div>',
                        unsafe_allow_html=True,
                    )
                if msg["role"] == "assistant" and show_debug and msg.get("contexts"):
                    with st.expander("Source excerpts"):
                        for i, ctx in enumerate(msg["contexts"], start=1):
                            category = ctx.get("document_category", "annual_report")
                            st.markdown(
                                f"**{i}.** {CATEGORY_LABELS.get(category, category)} — "
                                f"`{ctx['source']}` · page {ctx['page']} · relevance {ctx['score']:.3f}"
                            )
                            st.caption(ctx["text"][:400] + ("..." if len(ctx["text"]) > 400 else ""))

    prompt = st.chat_input("Ask about regulations, annual reports, insurance rules, or analyst exams...")

    if st.session_state.pending_prompt:
        pending = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        with chat_container:
            _run_query(pending, top_k=top_k, max_distance=max_distance)
    elif prompt:
        with chat_container:
            _run_query(prompt, top_k=top_k, max_distance=max_distance)

with tab_library:
    st.markdown(
        "Your indexed document library. All answers are retrieved from these PDFs with page citations."
    )
    _render_knowledge_base()
