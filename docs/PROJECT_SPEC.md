# Financial Compliance RAG — Technical Specification

---

## Document Control

| Field | Value |
|-------|-------|
| **Document** | PROJECT_SPEC.md |
| **Version** | 1.1 |
| **Status** | Active — Phase 1 complete |
| **Last updated** | 2026-07-07 |
| **Repository** | [github.com/jegadeesh17/FinancialComplianceRAG](https://github.com/jegadeesh17/FinancialComplianceRAG) |
| **Project folder** | `FinancialComplianceRAG` |
| **Related docs** | [README.md](../README.md), [PHASE_LOG.md](./PHASE_LOG.md) |

---

## 1. Executive Summary

This project delivers an **enterprise-grade Retrieval-Augmented Generation (RAG) system** for financial compliance document intelligence. Compliance and risk teams drown in fragmented regulatory PDFs (RBI, SEBI) and disclosure filings (10-K, annual reports). The system ingests PDFs, embeds chunks into ChromaDB, retrieves relevant passages, and generates **grounded, citation-backed answers** via OpenRouter — so every response is auditable and hallucination-resistant.

**Interview pitch:**

> *"Compliance teams drown in regulatory PDFs they can't search effectively. I built an enterprise RAG system that ingests RBI circulars and financial filings, chunks them semantically, stores embeddings in ChromaDB, and answers analyst questions via OpenRouter with mandatory page-level citations."*

---

## 2. Scope

### 2.1 In Scope

| # | Capability |
|---|------------|
| 1 | PDF ingestion (PyMuPDF) with page-level metadata |
| 2 | Semantic chunking (paragraph-aware, 800 chars / 100 overlap) |
| 3 | Local embeddings (`all-MiniLM-L6-v2`) + ChromaDB vector store |
| 4 | Top-k semantic retrieval with source metadata |
| 5 | OpenRouter LLM generation with strict context-only prompting |
| 6 | Streamlit chat UI with citation display (doc name + page) |
| 7 | Docker containerization |
| 8 | Per-phase pytest checkpoint tests |

### 2.2 Out of Scope

- Multi-user authentication / RBAC
- Local LLM inference (OpenRouter is the locked provider)
- OCR for scanned PDFs (text-based PDFs only)
- Hybrid BM25 + vector search (future improvement)
- Automated RAGAS / faithfulness evaluation suite (future improvement)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Module | Status |
|----|-------------|--------|--------|
| FR-01 | Load configuration from `.env` | `src/config.py` | ✅ |
| FR-02 | Extract text from PDFs with page metadata | `src/ingest_docs.py` | ✅ |
| FR-03 | Chunk text paragraph-aware (not naive char splits) | `src/ingest_docs.py` | ✅ |
| FR-04 | Embed chunks with Sentence-Transformers | `src/embeddings.py` | ✅ |
| FR-05 | Persist embeddings in ChromaDB | `src/vectorstore.py` | ✅ |
| FR-06 | Retrieve top-k similar chunks for a query | `src/retriever.py` | ✅ |
| FR-07 | Generate grounded answer via OpenRouter | `src/generator.py` | ✅ |
| FR-08 | End-to-end `query(question) -> RAGResponse` | `src/rag_pipeline.py` | ✅ |
| FR-09 | Streamlit chat UI with source citations | `app/app.py` | ✅ |
| FR-10 | Containerized deployment | `Dockerfile`, `docker-compose.yml` | ✅ |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Unit tests complete in < 60 s (no integration) | `pytest -v` |
| NFR-02 | Secrets never committed | `.env` gitignored |
| NFR-03 | Embeddings run on CPU (4GB VRAM laptops) | MiniLM on CPU |
| NFR-04 | OpenRouter HTTP timeout | 15 s connect / 45 s read |
| NFR-05 | Every answer includes source citations | doc name + page |
| NFR-06 | LLM answers strictly from retrieved context | grounded prompt |

---

## 4. Architecture

### 4.1 System Context

```text
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  PDF Corpus  │────▶│  PyMuPDF    │────▶│ Text Chunks  │
│ RBI/10-K/etc │     │  ingest     │     │ + metadata   │
└──────────────┘     └─────────────┘     └──────┬───────┘
                                                │
                       ┌─────────────┐          │
                       │  MiniLM     │◀─────────┘
                       │  embeddings │
                       └──────┬──────┘
                              │
                       ┌──────▼───────┐
                       │   ChromaDB   │
                       │  vector store│
                       └──────┬───────┘
                              │
User Question ──▶ Retriever ──┘
                      │
                      ▼
               Top-5 Chunks ──▶ OpenRouter LLM ──▶ Answer + Citations
                      │
                      ▼
               Streamlit Chat UI
```

### 4.2 Development Model

| Layer | Path | Role |
|-------|------|------|
| Orchestrator | `notebooks/FinancialComplianceRAG.ipynb` | Step-by-step lab; calls `src/` |
| Backend | `src/*.py` | Production logic; unit-tested |
| UI | `app/app.py` | Streamlit chat with citations |
| Spec | `docs/PROJECT_SPEC.md` | This document |
| Learning log | `docs/PHASE_LOG.md` | Per-phase notes |

### 4.3 Data Flow

```text
data/raw_pdfs/*.pdf
       │
       ▼  PyMuPDF — src/ingest_docs.py
  list[DocumentChunk]  {source, page, text}
       │
       ▼  Sentence-Transformers — src/embeddings.py
  vectors + metadata
       │
       ▼  ChromaDB — src/vectorstore.py
  persistent collection (data/chroma_db/)
       │
User query ──▶ src/retriever.py ──▶ top-k chunks
       │
       ▼  OpenRouter — src/generator.py
  RAGResponse {answer, citations[]}
       │
       ▼  Streamlit — app/app.py
  Chat UI with source sidebar
```

---

## 5. Configuration & Decisions Log

| Decision | Status | Value |
|----------|--------|-------|
| Project folder name | ✅ Locked | `FinancialComplianceRAG` |
| Domain | ✅ Locked | FinTech — Compliance-First Mixed Corpus |
| LLM provider | ✅ Locked | **OpenRouter** (`openrouter/free`) |
| Embedding model | ✅ Locked | `sentence-transformers/all-MiniLM-L6-v2` (CPU) |
| Vector DB | ✅ Locked | ChromaDB (persistent local) |
| Chunk size / overlap | ✅ Locked | 800 / 100 chars, paragraph-aware |
| Top-k retrieval | ✅ Locked | 5 chunks |
| Initial PDFs | ✅ Locked | 3 (1 RBI circular + 1 HDFC Bank annual report + 1 SEBI circular) |
| Full corpus target | ✅ Locked | 15–20 PDFs by Phase 6 |

### Environment Variables (`.env`)

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
CHROMA_PERSIST_DIR=data/chroma_db
RAW_PDF_DIR=data/raw_pdfs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
```

---

## 6. Dataset

### 6.1 Corpus (Compliance-First Mixed)

| Class | Share | Examples |
|-------|-------|----------|
| Regulatory circulars | ~40% | RBI Master Directions, SEBI circulars |
| Annual reports / 10-K | ~40% | HDFC Bank annual report, Reliance annual report |
| Insurance guidelines | ~20% | IRDAI guidelines |

### 6.2 Sample Evaluation Questions

- *"What is the minimum capital requirement in the RBI master direction?"*
- *"What KYC documents are required for individual customers?"*
- *"What is HDFC Bank's net interest income?"*
- *"What is HDFC Bank's total deposits as per the annual report?"*

---

## 7. Implementation Roadmap

**Gate rule:** Do not start phase *N+1* until phase *N* checkpoint tests pass.

| Phase | Name | Status | Checkpoint |
|-------|------|--------|------------|
| **1** | Project Setup & MLOps | ✅ Complete | `pytest tests/test_phase1_setup.py -v` |
| **2** | Document Ingestion | ✅ Complete | `pytest tests/test_phase2_ingest.py -v` |
| **3** | Embeddings & Vector Store | ✅ Complete | `pytest tests/test_phase3_vectorstore.py -v` |
| **4** | Retrieval System | ✅ Complete | `pytest tests/test_phase4_retriever.py -v` |
| **5** | LLM Generator | ✅ Complete | `pytest tests/test_phase5_generator.py -v` |
| **6** | Streamlit Chat UI | ✅ Complete | `pytest tests/test_phase6_dashboard.py -v` |
| **7** | Containerization (Docker) | ✅ Complete | `pytest tests/test_phase7_docker.py -v` |

**Status legend:** ⬜ Pending → 🟡 In Progress → ✅ Complete

---

## 8. Testing Strategy

| Type | Marker | When to Run |
|------|--------|-------------|
| Unit | default | Every change — fast, no network |
| Integration | `@pytest.mark.integration` | After ingest/retriever/generator changes |

```powershell
pytest -v                    # unit tests only (default)
pytest -m integration -v     # live API + real PDFs
```

---

## 9. File Manifest

```text
FinancialComplianceRAG/
├── app/app.py
├── data/raw_pdfs/              # gitignored
├── data/chroma_db/             # gitignored
├── docs/
│   ├── PROJECT_SPEC.md
│   └── PHASE_LOG.md
├── notebooks/FinancialComplianceRAG.ipynb
├── scripts/download_docs.py
├── src/
│   ├── config.py
│   ├── schemas.py
│   ├── ingest_docs.py
│   ├── embeddings.py
│   ├── vectorstore.py
│   ├── retriever.py
│   ├── generator.py
│   ├── rag_pipeline.py
│   └── chat.py
├── tests/test_phase1_setup.py … test_phase7_docker.py
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 10. Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-07-07 | 1.0 | Spec finalized; scaffold pushed to GitHub |
| 2026-07-07 | 1.1 | Initial PDFs updated to RBI + HDFC + SEBI |
| 2026-07-07 | 1.2 | Phase 1 complete — config, setup tests, data source guide |
| 2026-07-07 | 1.3 | Phase 2 complete — ingest pipeline and download script |
| 2026-07-07 | 1.4 | Phase 3 complete — embeddings, vectorstore, and ChromaDB persistence |
| 2026-07-07 | 1.5 | Phase 4 complete — retriever module and top-k semantic search tests |
| 2026-07-07 | 1.6 | Phase 5 complete — OpenRouter generator, citations, and checkpoint tests |
| 2026-07-07 | 1.7 | Phase 6 complete — rag_pipeline, chat helpers, Streamlit chat UI, UI tests |
| 2026-07-07 | 1.8 | Phase 7 complete — Dockerfile, compose stack, and containerization tests |
