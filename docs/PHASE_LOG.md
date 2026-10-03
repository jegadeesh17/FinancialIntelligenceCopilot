# Phase Log — Financial Intelligence Copilot

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
- Connected to [github.com/jegadeesh17/FinancialIntelligenceCopilot](https://github.com/jegadeesh17/FinancialIntelligenceCopilot)

### Concepts
- **Compliance-first RAG:** Lead with the pain point (regulatory PDF search), not just "chat with PDFs"
- **Citations are mandatory:** In regulated finance, every AI answer needs an audit trail (doc + page)
- **Spec before code:** PROJECT_SPEC.md is the contract; phases implement against it

### Locked decisions
- Project name: `FinancialIntelligenceCopilot`
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

---

## Phase 6 — Streamlit Chat UI

**Completed:** 2026-07-07

### What we built
- `src/rag_pipeline.py` — end-to-end `ask_question()` orchestration (retrieve → generate)
- `src/chat.py` — chat session-state helpers + citation formatting
- `app/app.py` — Streamlit chat interface with history, spinner, and source citations
- `tests/test_phase6_dashboard.py` — chat helpers, pipeline wiring, and Streamlit `AppTest` smoke tests
- Notebook Steps 9–10 wired (sample Q&A loop + deployment command)

### Concepts
- **Pipeline boundary:** UI calls one function (`ask_question`) instead of manually wiring retriever/generator each time
- **Session state chat log:** Messages persist across reruns for conversational UX
- **UI testability:** `streamlit.testing.v1.AppTest` enables headless app validation in pytest

### Checkpoint
4 unit tests passed and 1 integration UI test passed.

```powershell
pytest tests/test_phase6_dashboard.py -v
pytest tests/test_phase6_dashboard.py -m integration -v
```

### UI enhancement pass (2026-07-07)
- Added sidebar controls (`top_k`, clear chat, context debug toggle)
- Added index status panel (indexed chunk count + PDF count)
- Added expandable retrieved-context view with score/source/page
- Improved citation rendering by grouping pages per source

---

## Phase 7 — Containerization (Docker)

**Completed:** 2026-07-07

### What we built
- `Dockerfile` — Python 3.11 image, installs dependencies, runs Streamlit app
- `docker-compose.yml` — app service, port mapping (`8501:8501`), `.env` injection, data volume mounts
- `.dockerignore` — excludes local/dev artifacts from image build context
- `tests/test_phase7_docker.py` — Docker artifact checks + optional `docker compose config` validation

### Concepts
- **Reproducible runtime:** App can run with consistent dependencies inside a container
- **Data persistence:** PDF corpus and ChromaDB storage mounted via compose volumes
- **Portable launch:** `docker compose up --build` brings up the full app service

### Checkpoint
4 tests passed (plus optional compose validation when Docker is available).

```powershell
pytest tests/test_phase7_docker.py -v
```

---

## Phase 8 — Corpus Ops (Legacy Notes)

**Completed:** 2026-07-09

### What we built
- Consolidated corpus operations around existing utilities:
  - `scripts/download_docs.py` for optional source download bootstrap
  - `scripts/build_index.py` for index rebuild and metadata refresh
  - `scripts/eval_retrieval.py` for retrieval hit-rate checks

### Concepts
- **Source authority:** official PDFs remain the source of truth for RAG ingestion
- **Batch-first refresh:** corpus updates happen offline, not during `/ask`
- **Portfolio practicality:** enough automation for demos without scheduler/service sprawl

### Checkpoint
- Existing corpus utilities compile and run as standalone utilities.

```powershell
python scripts/download_docs.py
python scripts/build_index.py
python scripts/eval_retrieval.py
```

---

## Phase 9 — Confidence Gate + Metadata Propagation

**Completed:** 2026-07-09

### What we built
- Retrieval confidence threshold in `src/config.py` + `src/retriever.py`
- `low_confidence` + `best_score` added across pipeline/API/UI
- Metadata contract expanded in `src/schemas.py` and propagated:
  - `source_url`, `retrieved_at`, `regulator`, `company`, `document_vertical`
- Ingestion now reads `earnings_manifest.json` and auto-tags chunks
- Added `src/corpus_stats.py` and exposed corpus coverage via `/health` and Streamlit sidebar

### Concepts
- **Confidence-aware RAG:** when retrieval quality is weak, communicate uncertainty explicitly
- **End-to-end metadata lineage:** ingest → vectorstore → retrieval → API response
- **Dual-vertical observability:** visibility into compliance/earnings mix avoids hidden data skew

### Checkpoint
- Target tests passed after these changes.

```powershell
pytest tests/test_phase2_ingest.py tests/test_phase4_retriever.py tests/test_api.py -q
```

---

## Phase 10 — Hardening, Resume Unification, and Cleanup

**Status:** Complete (2026-07-09)

### Completed
- Consolidated to one integrated resume: `ZGeneral/Jegadeesh_D_Course_Model_Resume.md`
- Moved stale ZGeneral files to `.trash/20260709/`
- **Phase 10A:** Dual-vertical UI (vertical metrics, sample queries, confidence badges, market snapshot timestamp)
- **Phase 10B:** Hardened core test coverage (`tests/test_api.py`, retrieval/config checks, corpus stats checks)
- **Phase 10C:** Updated `README.md` and `docs/DEMO.md` with dual-vertical demo flow
- **Phase 10D:** Verification run (`pytest -m "not integration" -q`, index build, retrieval eval)
- **Phase 10E:** Archived local `AgenticMarketResearcher` to `.trash/20260709/`

### Checkpoint
```powershell
pytest -m "not integration" -q
python scripts/build_index.py
python scripts/eval_retrieval.py
streamlit run app/app.py
```

---

## Tomorrow Plan — Remaining Phases (2026-07-09 Morning)

**All items below completed on 2026-07-09.**

### Phase 10A — Dual-Vertical UX Completion ✅
### Phase 10B — Hardening Tests ✅
### Phase 10C — Docs Sync ✅
### Phase 10D — Manual Verification ✅
### Phase 10E — AgenticMarketResearcher Archive ✅

---

## Phase 11 — Evaluation, Hybrid Default, and Cleanup (2026-10-03)

- Hybrid BM25 + dense retrieval (RRF) is the default in the API (`ENABLE_HYBRID_SEARCH`).
- Added `scripts/eval_ragas.py`: RAGAS faithfulness, response relevancy and context precision, judged by `deepseek/deepseek-v4.1-flash`, generator `openai/gpt-oss-20b`. Results (n=10, dense / hybrid): faithfulness 0.620 / 0.627, relevancy 0.489 / 0.696, context precision 0.353 / 0.228. Reports: `reports/ragas_eval.json`, `reports/RAGAS_EVAL.md`.
- Lesson: the free `openrouter/free` generator was unreliable (1/10 dense and 5/10 hybrid answers were generation failures scored 0.0), so evaluation uses one fixed paid model.
- Lesson: in the lowest-faithfulness HDFC numeric questions the retrieved chunks did not contain the figures, and the generator stated numbers anyway.
- Fixed latency benchmarking: added a warm-up call so model load is no longer counted (P95 dense 7,483 ms -> 39.7 ms) and replaced a hard-coded "<150 ms SLA" claim with measured values.
- Removed the Streamlit UI (`app/`, `src/chat.py`, `src/ui_styles.py`, Streamlit tests, compose service). The FastAPI-served web UI is the only UI.
- Split `requirements-dev.txt` (pytest, RAGAS) from `requirements.txt` so the production image stays lean.
- Added `GET /eval` and an "Eval metrics" popover in the web UI; refreshed the front page header and compacted the layout to one screen.
