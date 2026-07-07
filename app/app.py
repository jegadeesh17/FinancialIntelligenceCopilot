import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chat import append_message, format_citations, init_chat_state
from src.generator import generate_answer
from src.indexing import read_index_metadata
from src.retriever import retrieve
from src.telemetry import log_query
from src.vectorstore import build_vector_index, get_chroma_client, get_collection_count, get_or_create_collection

st.set_page_config(page_title="Financial Compliance RAG", layout="wide")
st.title("Financial Compliance RAG")
st.caption("Enterprise RAG for regulatory PDFs and financial filings.")

with st.sidebar:
    st.subheader("RAG Controls")
    top_k = st.slider("Top-k retrieval", min_value=1, max_value=10, value=5, step=1)
    max_distance = st.slider("Max retrieval distance", min_value=0.0, max_value=2.0, value=1.2, step=0.05)
    show_debug = st.toggle("Show retrieved context", value=False)
    clear_chat = st.button("Clear chat")

    pdf_count = len(list((PROJECT_ROOT / "data" / "raw_pdfs").glob("*.pdf")))
    try:
        vector_count = get_collection_count()
    except Exception:
        vector_count = 0
    meta = read_index_metadata()
    st.markdown("---")
    st.caption(f"Indexed chunks: **{vector_count}**")
    st.caption(f"PDFs available: **{pdf_count}**")
    st.caption(f"Last indexed: **{meta.get('last_indexed_at', 'unknown')}**")
    if vector_count == 0:
        st.warning("Index is empty. Run `build_vector_index()` once.")

    confirm_rebuild = st.checkbox("Confirm rebuild index")
    if st.button("Rebuild index", disabled=not confirm_rebuild):
        with st.spinner("Rebuilding vector index..."):
            stored = build_vector_index()
        st.success(f"Rebuilt index with {stored} chunks.")
        st.rerun()

init_chat_state()
if clear_chat:
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()

main_col, docs_col = st.columns([3, 2])

with main_col:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown("**Summary**")
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                st.markdown("**Citations**")
                st.caption(format_citations(msg.get("citations", [])))
            if msg["role"] == "assistant" and show_debug and msg.get("contexts"):
                with st.expander("Retrieved context"):
                    for i, ctx in enumerate(msg["contexts"], start=1):
                        st.markdown(
                            f"**{i}.** `{ctx['source']}` p.{ctx['page']} | score={ctx['score']:.4f}\n\n"
                            f"{ctx['text'][:320]}..."
                        )

    if prompt := st.chat_input("Ask a compliance question..."):
        append_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving context and generating answer..."):
                start = time.perf_counter()
                try:
                    contexts = retrieve(prompt, top_k=top_k, max_distance=max_distance)
                    response = generate_answer(prompt, contexts)
                    st.markdown("**Summary**")
                    st.markdown(response.answer)
                    st.markdown("**Citations**")
                    st.caption(format_citations(response.citations))
                    append_message("assistant", response.answer, response.citations)
                    st.session_state.messages[-1]["contexts"] = [
                        {
                            "source": c.source,
                            "page": c.page,
                            "score": c.score,
                            "text": c.text,
                        }
                        for c in contexts
                    ]
                    latency_ms = (time.perf_counter() - start) * 1000
                    top_sources = [c.source for c in contexts[:top_k]]
                    fallback_used = len(contexts) == 0 or "could not find relevant context" in response.answer.lower()
                    log_query(prompt, top_sources=top_sources, fallback_used=fallback_used, latency_ms=latency_ms)
                    if fallback_used:
                        st.info("Insufficient evidence found. Try broadening query or updating corpus.")
                except Exception as exc:  # pragma: no cover
                    message = f"Error: {exc}"
                    st.error(message)
                    append_message("assistant", message, [])

with docs_col:
    st.subheader("Document Management")
    pdf_files = sorted((PROJECT_ROOT / "data" / "raw_pdfs").glob("*.pdf"))
    collection = get_or_create_collection(get_chroma_client())
    rows = collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for md in rows.get("metadatas", []):
        if not md:
            continue
        source = str(md.get("source", ""))
        counts[source] = counts.get(source, 0) + 1

    docs_data = []
    for pdf_file in pdf_files:
        chunk_count = counts.get(pdf_file.name, 0)
        docs_data.append(
            {
                "Document": pdf_file.name,
                "SizeMB": round(pdf_file.stat().st_size / (1024 * 1024), 2),
                "IndexedChunks": chunk_count,
                "Status": "Indexed" if chunk_count > 0 else "Pending",
            }
        )
    if docs_data:
        st.dataframe(docs_data, use_container_width=True, hide_index=True)
    else:
        st.info("No PDFs found in data/raw_pdfs.")
