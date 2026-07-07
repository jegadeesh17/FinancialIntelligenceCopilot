# Phase Log — Financial Compliance RAG

> Full build specification: [PROJECT_SPEC.md](./PROJECT_SPEC.md)

Use this file to capture what you learned each phase.

---

## Scaffold — Project Structure & Spec

**Completed:** 2026-07-07

### What we built
- Standard project scaffold via `create_project.py`
- `docs/PROJECT_SPEC.md` — finalized technical specification (v1.0)
- `docs/PHASE_LOG.md` — this learning log
- `README.md` — standard portfolio layout
- `.env.example`, `pytest.ini`, `requirements.txt` (RAG dependencies)
- `tests/test_phase0_scaffold.py` — structure checkpoint (scaffold only)
- Connected to [github.com/jegadeesh17/FinancialComplianceRAG](https://github.com/jegadeesh17/FinancialComplianceRAG)

### Concepts
- **Compliance-first RAG:** Lead with the pain point (regulatory PDF search), not just "chat with PDFs"
- **Citations are mandatory:** In regulated finance, every AI answer needs an audit trail (doc + page)
- **Spec before code:** PROJECT_SPEC.md is the contract; phases implement against it

### Locked decisions
- Project name: `FinancialComplianceRAG`
- Corpus: ~40% regulatory / ~40% annual reports / ~20% insurance
- LLM: OpenRouter (`openrouter/free`)
- Embeddings: `all-MiniLM-L6-v2` on CPU
- Vector DB: ChromaDB
- Initial PDFs: 3 (1 RBI + 1 HDFC Bank annual report + 1 SEBI circular)

### Checkpoint command
```powershell
pytest tests/test_phase0_scaffold.py -v
```

---

## Phase 1 — Project Setup & MLOps Foundation

**Completed:** 2026-07-07

### What we built
- `src/config.py` — Pydantic Settings for paths, chunking, LLM, and embedding config
- `tests/test_phase1_setup.py` — structure, import, and config validation tests
- `docs/DATA_SOURCES.md` — where to get the 3 initial PDFs (manual vs script in Phase 2)

### Concepts
- **Pydantic Settings:** Type-safe `.env` loading with defaults and validation
- **`chroma_path` / `raw_pdf_path`:** Resolved relative to project root for portable paths
- **Chunk overlap validation:** `chunk_overlap` must stay smaller than `chunk_size`

### Checkpoint
21 tests passed.

```powershell
pip install -r requirements.txt
pytest tests/test_phase1_setup.py -v
```

---

## Phase 2 — Document Ingestion

**Completed:** 2026-07-07

### What we built
- `src/schemas.py` — `DocumentChunk` Pydantic model (`source`, `page`, `text`, `chunk_index`)
- `src/ingest_docs.py` — PyMuPDF extraction + paragraph-aware chunking
- `scripts/download_docs.py` — auto-download RBI / HDFC / SEBI PDFs (with manual fallback)
- `tests/test_phase2_ingest.py` — chunking, extraction, and ingest checkpoint tests
- Notebook Steps 1–3 wired (config, PDF listing, ingest)

### Concepts
- **Paragraph-aware chunking:** Split on `\n\n` first; only hard-split when a paragraph exceeds `chunk_size`
- **Page metadata:** Every chunk keeps `source` (filename) and `page` (1-indexed) for citations
- **Download script:** Government/bank URLs change often — script validates `%PDF` magic bytes; manual fallback documented

### Download status (2026-07-07)
- ✅ `rbi_master_direction_kyc.pdf` — auto-download works
- ✅ `sebi_circular_disclosure.pdf` — auto-download works
- ⚠️ `hdfc_bank_annual_report.pdf` — large file; may timeout. Download manually from [HDFC IR](https://www.hdfcbank.com/personal/about-us/investor-relations/annual-reports) if script fails.


```powershell
pytest tests/test_phase2_ingest.py -v
python scripts/download_docs.py   # optional — fetch real PDFs
pytest tests/test_phase2_ingest.py -m integration -v   # needs PDFs in data/raw_pdfs/
```

---

## Phase 3 — Embeddings & Vector Store

**Completed:** 2026-07-07

### What we built
- `src/embeddings.py` — MiniLM model loader + `embed_texts` / `embed_query`
- `src/vectorstore.py` — persistent ChromaDB client, collection management, batched upserts
- `tests/test_phase3_vectorstore.py` — embedding, persistence, idempotency, and full-corpus integration checks
- Notebook Steps 5–6 wired (embedding dimension check + index build)

### Concepts
- **Embedding dimension:** `all-MiniLM-L6-v2` outputs 384-dimensional vectors
- **Persistent vector store:** ChromaDB persists to `data/chroma_db/` for reuse between runs
- **Batch upsert:** Large corpora must be written in batches to respect Chroma max batch limits

### Checkpoint
8 unit tests passed and 1 integration test passed.

```powershell
pytest tests/test_phase3_vectorstore.py -v
pytest tests/test_phase3_vectorstore.py -m integration -v
```

---

## Phase 4 — Retrieval System

**Completed:** 2026-07-07

### What we built
- `src/retriever.py` — query embedding + Chroma top-k retrieval with metadata and score
- `src/schemas.py` — `RetrievalResult` model for typed retrieval outputs
- `tests/test_phase4_retriever.py` — unit and integration checkpoint tests
- Notebook Step 7 wired (retrieval demo against indexed corpus)

### Concepts
- **Top-k retrieval:** `n_results` defaults to `settings.top_k`, override per query when needed
- **Grounding payload:** Retrieval returns `source`, `page`, `chunk_index`, `text`, and distance `score`
- **Empty-safe behavior:** blank query or empty collection returns `[]` (no downstream crash)

### Checkpoint
4 unit tests passed and 1 integration test passed.

```powershell
pytest tests/test_phase4_retriever.py -v
pytest tests/test_phase4_retriever.py -m integration -v
```

---

## Phase 5 — LLM Generator

**Completed:** 2026-07-07

### What we built
- `src/generator.py` — OpenRouter call wrapper, grounded prompt builder, citation-aware response assembly
- `src/schemas.py` — `Citation` and `RAGResponse` models
- `tests/test_phase5_generator.py` — prompt, guardrails, mocked generation, and optional live integration checks
- Notebook Step 8 wired (retrieve + generate + citation display)

### Concepts
- **Grounded prompting:** LLM is instructed to answer strictly from retrieved context
- **Guardrails:** Empty question and empty context produce safe deterministic responses
- **Citations:** Output carries structured source/page references for auditability

### Checkpoint
4 unit tests passed. Integration test is environment-dependent and skipped without `OPENROUTER_API_KEY`.

```powershell
pytest tests/test_phase5_generator.py -v
pytest tests/test_phase5_generator.py -m integration -v
```
