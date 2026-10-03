# Financial Intelligence Copilot
---
### **Project Overview**
**Financial Intelligence Copilot** is a Retrieval-Augmented Generation system for BFSI document intelligence. It ingests manually curated PDFs (regulatory circulars, annual reports, insurance guidelines, exam reference material), embeds them into ChromaDB, and answers questions via OpenRouter with **page-level citations** and retrieval confidence signals.

**Interview pitch:** *"I built Financial Intelligence Copilot — a dual-vertical RAG system that answers compliance and earnings questions from RBI/SEBI circulars and annual-report PDFs, with ChromaDB retrieval, confidence gating, and auditable page-level citations."*

**Live demo:** [https://financial-copilot-api-242711953247.asia-south1.run.app/app](https://financial-copilot-api-242711953247.asia-south1.run.app/app)  
**Repository:** [github.com/jegadeesh17/FinancialIntelligenceCopilot](https://github.com/jegadeesh17/FinancialIntelligenceCopilot)  
**Full specification:** [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)  
**Learning log:** [docs/PHASE_LOG.md](docs/PHASE_LOG.md)  
**API reference:** [docs/API.md](docs/API.md)  
**Deployment guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---
### **Key Features**
- PDF ingestion with PyMuPDF and page-level metadata (Phase 2)
- Paragraph-aware semantic chunking (800 chars / 100 overlap)
- Local CPU embeddings (`all-MiniLM-L6-v2`) + ChromaDB vector store
- Top-k retrieval with source metadata
- Hybrid retrieval: dense vectors + BM25 fused with Reciprocal Rank Fusion (on by default)
- OpenRouter LLM generation with strict context-only prompting
- Web UI served by FastAPI (`/app`) with citation display (doc name + page)
- RAGAS answer-quality evaluation (faithfulness, relevancy, context precision), also viewable in the app via **Eval metrics** (`GET /eval`)
- Checkpoint tests per phase (`pytest tests/test_phaseN_*.py`)

---
### **Dataset**
- **Corpus composition:** compliance/regulatory PDFs and financial-report PDFs
- **Current indexed size:** run `python scripts/build_index.py` and check `/health`
- **Storage:** `data/raw_pdfs/` (gitignored), vectors in `data/chroma_db/` (gitignored)
- **Manual PDF guide:** [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)

**Sample questions:**
- *"What is the minimum capital requirement in the RBI master direction?"*
- *"What is HDFC Bank's net interest income?"*

---
### **Project Structure**
```text
FinancialIntelligenceCopilot/
├── .github/workflows/          # CI (tests) and Cloud Run deploy
├── api/                        # FastAPI service + web UI (index.html)
├── configs/                    # Pydantic settings
├── data/
│   ├── raw_pdfs/               # PDF corpus (gitignored)
│   └── chroma_db/              # Vector store (gitignored)
├── docs/
│   ├── PROJECT_SPEC.md         # Master technical specification
│   ├── PHASE_LOG.md            # Per-phase learning notes
│   ├── API.md                  # Endpoint reference
│   ├── DEPLOYMENT.md           # Cloud Run pipeline, secrets, rollback
│   ├── DEMO.md                 # 5-minute demo flow
│   └── DATA_SOURCES.md         # PDF download guide
├── notebooks/                  # RAG workflow notebook
├── reports/                    # Retrieval + RAGAS evaluation outputs
├── scripts/                    # Index build, retrieval and RAGAS evaluation scripts
├── src/                        # Core Python modules
├── tests/                      # Phase checkpoint tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # + pytest and RAGAS (dev/eval only)
├── .env.example
├── LICENSE
└── README.md
```

---
### **How It Works**
1. **Ingest** — PyMuPDF extracts text from PDFs with page metadata (`src/ingest_docs.py`).
2. **Chunk** — Paragraph-aware splitting preserves semantic meaning (`src/ingest_docs.py`).
3. **Embed** — Sentence-Transformers converts chunks to vectors (`src/embeddings.py`).
4. **Store** — ChromaDB persists embeddings + metadata (`src/vectorstore.py`).
5. **Retrieve** — User query → top-5 chunks, dense vectors fused with BM25 via RRF by default (`src/retriever.py`).
6. **Generate** — OpenRouter LLM answers strictly from context (`src/generator.py`).
7. **Serve** — FastAPI exposes `/ask`, and the web UI (`api/index.html`) displays the answer + citations.

---
### **Build Progress**
| Phase | Name | Status |
|-------|------|--------|
| 0 | Scaffold & Spec | ✅ Complete |
| 1 | Project Setup & MLOps | ✅ Complete |
| 2 | Document Ingestion | ✅ Complete |
| 3 | Embeddings & Vector Store | ✅ Complete |
| 4 | Retrieval System | ✅ Complete |
| 5 | LLM Generator | ✅ Complete |
| 6 | Chat UI (Streamlit, since replaced by the FastAPI-served web UI) | ✅ Complete |
| 7 | Containerization (Docker) | ✅ Complete |
| 8 | Corpus Ops | ✅ Complete |
| 9 | Confidence Gate + Metadata Propagation | ✅ Complete |
| 10 | Hardening, Resume Unification, Cleanup | ✅ Complete |
| 11 | Evaluation, Hybrid Default, Cleanup | ✅ Complete |

Run scaffold test: `pytest tests/test_phase0_scaffold.py -v`  
Full spec: [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)

### **Quickstart**
Requires Python 3.11.
```powershell
git clone https://github.com/jegadeesh17/FinancialIntelligenceCopilot.git
cd FinancialIntelligenceCopilot
python -m venv .venv
.venv\Scripts\activate             # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt    # requirements-dev.txt also adds pytest and RAGAS
cp .env.example .env               # add OPENROUTER_API_KEY
python scripts/build_index.py
uvicorn api.main:app --port 8000   # then open http://localhost:8000/app
```

Run the tests with `pytest -q`. To explore the pipeline step by step, open `notebooks/FinancialIntelligenceCopilot.ipynb`.

Interactive API docs are at `/docs`; see [docs/API.md](docs/API.md) for the full reference. If `API_KEY` is set in `.env`, call `/ask` with header `x-api-key: <your-key>`.

**Retrieval evaluation:**
```powershell
python scripts/eval_retrieval.py
```

---
### **Retrieval Evaluation**
- Eval set: `data/eval_questions.json` (10 questions)
- Script: `python scripts/eval_retrieval.py`
- Report: `reports/retrieval_eval.json` and [reports/evaluation.md](reports/evaluation.md)
- Target: ≥ 70% retrieval hit rate
- Dense vs hybrid benchmark: `python scripts/eval_rag_metrics.py` → [reports/EVALUATION_BENCHMARK.md](reports/EVALUATION_BENCHMARK.md)

| Metric (top-5, n=10) | Dense | Hybrid (BM25 + RRF) |
| :--- | :---: | :---: |
| Hit rate | 70.0% (7/10) | 70.0% (7/10) |
| MRR | 0.525 | 0.550 |
| Precision@5 | 0.380 | 0.360 |
| P95 latency (local CPU, warm) | 39.7 ms | 43.9 ms |

---
### **Answer-quality evaluation**
- Eval set: same 10 questions in `data/eval_questions.json` (n=10, no reference answers)
- Script: `python scripts/eval_ragas.py` (dense) and `python scripts/eval_ragas.py --hybrid`
- Report: `reports/ragas_eval.json` and [reports/RAGAS_EVAL.md](reports/RAGAS_EVAL.md)
- Also shown live in the app: click **Eval metrics** (top right of the [web UI](https://financial-copilot-api-242711953247.asia-south1.run.app/app)), backed by `GET /eval`.
- Generator: `openai/gpt-oss-20b` (paid endpoint, no fallbacks). Judge: `deepseek/deepseek-v4.1-flash` via OpenRouter, with local MiniLM embeddings. RAGAS 0.4.3.

| Metric (mean, n=10) | Dense | Hybrid (BM25 + RRF) |
| :--- | :---: | :---: |
| Faithfulness | 0.620 | 0.627 |
| Response relevancy | 0.489 | 0.696 |
| Context precision (no reference) | 0.353 | 0.228 |
| NaN scores / generation failures | 0 / 0 | 0 / 0 |

**Caveats**
- Small sample: with n=10, one question moves a mean by 0.1, so differences between dense and hybrid are not statistically meaningful.
- The judge is a single LLM and is noisy. Response relevancy is computed from 1 generated question per answer, not 3, because OpenRouter ignores the `n` parameter.
- The retrieval eval uses wide `expected_page` ranges (for example 1–500 for the annual report), so its hit rate is lenient.
- In the lowest-faithfulness rows (HDFC numeric questions), the needed figures were not in the retrieved chunks and the generator stated numbers anyway.
- Free-tier generation (`openrouter/free`) was tried first and rejected: 1/10 (dense) and 5/10 (hybrid) answers were generation failures, so those runs are not reported.

---
### **Demo Script**
See [docs/DEMO.md](docs/DEMO.md) for a 5-minute interview demo flow.

**Quick demo loop:**
1. Run `python scripts/build_index.py` after adding PDFs to `data/raw_pdfs/`.
2. Ask a regulatory, annual report, or exam-reference question in the web UI (`/app`).
3. Check the cited document and page under each answer.

---
```powershell
# Docker deployment
docker compose up --build
```

---
### **Technology Stack**
| Layer | Technology |
|-------|------------|
| PDF parsing | PyMuPDF |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (CPU) |
| Vector DB | ChromaDB |
| LLM | OpenRouter (primary + optional fallback chain) |
| Retrieval | Dense + BM25 (`rank-bm25`) fused with RRF |
| Frontend | Static HTML/JS served by FastAPI |
| Evaluation (dev only) | RAGAS |
| Config | Pydantic Settings |
| Tests | pytest |
| Deploy | Docker → GCP Cloud Run via GitHub Actions |

---
### **Example Use Case**
A compliance analyst at a bank receives an updated RBI Master Direction on KYC requirements. Instead of reading 80 pages, they ask: *"What KYC documents are required for individual customers?"* The system retrieves the relevant paragraph, generates a grounded answer, and cites **RBI_Master_Direction_KYC.pdf, Page 12**.

---
### **Future Improvements**
- OCR for scanned PDFs
- Multi-collection routing (regulatory vs. filings)

---
### **Contributors**
- [jegadeesh17](https://github.com/jegadeesh17)

---
### **License**
MIT, see [LICENSE](LICENSE).
