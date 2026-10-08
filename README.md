# Financial Intelligence Copilot

A Retrieval-Augmented Generation (RAG) system that answers questions over 12 BFSI PDFs (RBI, SEBI and IRDAI documents, annual reports, an exam workbook) with page-level citations and a retrieval low-confidence flag.

**Live demo:** https://financial-copilot-api-242711953247.asia-south1.run.app/app
**Repository:** https://github.com/jegadeesh17/FinancialIntelligenceCopilot

## Features

- PDF ingestion with PyMuPDF and page-level metadata.
- Paragraph-based chunking (800 characters, 100 overlap); a single paragraph longer than 800 characters is hard-split by characters.
- Local CPU embeddings (`all-MiniLM-L6-v2`) stored in a persistent ChromaDB collection.
- Top-5 retrieval. With hybrid search on (the `/ask` default), the 15 closest dense candidates are re-ranked by BM25 using weighted Reciprocal Rank Fusion (k=60, BM25 weight 0.5, hard-coded).
- OpenRouter generation with a context-only prompt, retries, and an optional fallback-model list (empty by default).
- Citations (document name and page) on every generated answer, plus `low_confidence` and `best_score` fields.
- Web UI served by FastAPI at `/app`, with an **Eval metrics** popover backed by `GET /eval`.
- RAGAS answer-quality evaluation (faithfulness, response relevancy, context precision).

## Quick start

Prerequisites: Python 3.11 (CI, `runtime.txt` and the Dockerfile all use 3.11) and an OpenRouter API key.

```powershell
git clone https://github.com/jegadeesh17/FinancialIntelligenceCopilot.git
cd FinancialIntelligenceCopilot
python -m venv .venv
.venv\Scripts\activate             # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt    # requirements-dev.txt also adds pytest and RAGAS
cp .env.example .env               # set OPENROUTER_API_KEY
# add the PDFs to data/raw_pdfs/ (see docs/DATA_SOURCES.md), then:
python scripts/build_index.py
uvicorn api.main:app --port 8000   # then open http://localhost:8000/app
```

Docker: `docker compose up --build` (needs `.env`; serves on http://localhost:8080).

## Usage

Open `http://localhost:8000/app`, or call the API. Interactive docs are at `/docs`; the full reference is [docs/API.md](docs/API.md).

```bash
curl http://localhost:8000/health
```

Output from a local run on 2026-10-03 (copied unformatted):

```json
{"status":"ok","chunk_count":12075,"corpus":{"total_pdfs":12,"category_counts":{"regulatory":4,"annual_report":5,"insurance":2,"exam_reference":1},"category_shares":{"regulatory":0.333,"annual_report":0.417,"insurance":0.167,"exam_reference":0.083},"regulator_counts":{"IRDAI":2,"RBI":2,"SEBI":2}},"index_metadata":{"last_indexed_at":"2026-07-13T16:49:32.953283+00:00","chunk_count":12075,"pdf_count":12,"embedding_model":"sentence-transformers/all-MiniLM-L6-v2","chunk_size":800,"chunk_overlap":100}}
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What KYC documents are required for individual customers?", "hybrid": true}'
```

Response shape (from `AskResponse` in `api/main.py`; values are placeholders, not a recorded answer):

```json
{
  "answer": "<string>",
  "citations": [{"source": "<pdf filename>", "page": 0}],
  "model": "<model that answered>",
  "low_confidence": false,
  "best_score": 0.0,
  "source_chunks": [{"source": "", "page": 0, "text": "", "score": 0.0, "retrieved_at": "", "regulator": "", "document_category": ""}]
}
```

If `API_KEY` is set on the server, add the header `x-api-key: <your-key>`. A 5-minute demo flow is in [docs/DEMO.md](docs/DEMO.md). To rebuild the index after changing PDFs, rerun `python scripts/build_index.py`.

Sample questions: *"What is the minimum capital requirement in the RBI master direction?"*, *"What is HDFC Bank's net interest income?"*, *"What KYC documents are required for individual customers?"* (the last one answers from `rbi_master_direction_kyc.pdf` with a page citation).

## Running tests

```bash
.venv/Scripts/python -m pytest -q                      # full default run
.venv/Scripts/python -m pytest tests/test_api.py -q    # one file
.venv/Scripts/python -m pytest -m integration -v       # live network tests (deselected by default)
```

Measured on 2026-10-03: 86 tests collected; the default run (`pytest.ini` adds `-m "not integration"`) selects 82 and deselects 4 `integration` tests. Result: `82 passed, 4 deselected`. CI runs `pytest -m "not integration" -q` on every push and pull request.

## Configuration

Settings are read from `.env` (template: [.env.example](.env.example)) by `configs/settings.py`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | empty | OpenRouter key; empty is treated as missing |
| `OPENROUTER_MODEL` | `openrouter/free` | Model slug |
| `OPENROUTER_FALLBACK_MODELS` | empty | Comma-separated fallback slugs tried after the primary |
| `LLM_MAX_RETRIES` | `3` | Attempts per model (1 to 5) |
| `API_KEY` | empty | If set, `/ask` requires header `x-api-key` |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | `/ask` requests per client IP per minute (in memory, per instance) |
| `CHROMA_PERSIST_DIR` | `data/chroma_db` | ChromaDB directory |
| `RAW_PDF_DIR` | `data/raw_pdfs` | Source PDF directory |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `800` / `100` | Chunking, in characters |
| `TOP_K` | `5` | Chunks passed to the generator |
| `LOW_CONFIDENCE_DISTANCE` | `0.85` | Best distance above this sets `low_confidence` |
| `ENABLE_HYBRID_SEARCH` | `true` | Default for the `hybrid` field of `/ask` |
| `HYBRID_ALPHA`, `LLM_PROVIDER`, `ENVIRONMENT`, `LOG_LEVEL`, `PORTKEY_API_KEY`, `PORTKEY_GATEWAY_URL` | see `.env.example` | Defined in settings but not read by the current code |

## Project structure

```text
FinancialIntelligenceCopilot/
├── .github/workflows/          # ci.yml (tests), deploy.yml (Cloud Run)
├── api/                        # FastAPI service (main.py) + web UI (index.html)
├── configs/                    # Pydantic settings
├── data/                       # eval_questions.json; raw_pdfs/ and chroma_db/ are gitignored
├── docs/                       # specification, API, deployment, evaluation, decisions
├── logs/  models/              # placeholders (.keep)
├── notebooks/                  # RAG workflow notebook
├── reports/                    # retrieval, benchmark and RAGAS outputs (reports/*.json feed GET /eval)
├── scripts/                    # index build, PDF download, retrieval and RAGAS evaluation
├── src/                        # core Python modules
├── tests/                      # pytest suite
├── CHANGELOG.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── pytest.ini
├── requirements.txt            # production dependencies
├── requirements-dev.txt        # adds pytest and RAGAS (dev/eval only)
├── runtime.txt
└── .env.example
```

## Architecture

1. **Ingest:** PyMuPDF extracts text per page (`src/ingest_docs.py`).
2. **Chunk:** split on paragraphs, merged up to 800 characters with 100 overlap; oversized paragraphs are split by characters (`src/ingest_docs.py`).
3. **Embed:** Sentence-Transformers MiniLM on CPU (`src/embeddings.py`).
4. **Store:** ChromaDB persistent collection with `source`, `page`, `retrieved_at`, `regulator` and `document_category` metadata (`src/vectorstore.py`).
5. **Retrieve:** dense top-k; with hybrid on, 15 dense candidates are re-ranked by BM25 with weighted RRF and cut to 5 (`src/retriever.py`).
6. **Generate:** OpenRouter answers strictly from the retrieved context (`src/generator.py`).
7. **Serve:** FastAPI exposes `/ask`, `/health`, `/eval`; the UI is `api/index.html`.

| Layer | Technology |
|-------|------------|
| PDF parsing | PyMuPDF |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (CPU) |
| Vector DB | ChromaDB |
| LLM | OpenRouter (primary model, retries, optional fallback list) |
| Retrieval | Dense, optionally BM25 (`rank-bm25`) re-ranked with RRF |
| Frontend | Static HTML/JS served by FastAPI |
| Evaluation (dev only) | RAGAS |
| Config | Pydantic Settings |
| Deploy | Docker, GCP Cloud Run via GitHub Actions |

**Corpus (12 PDFs):** 5 annual reports (HDFC Bank, ICICI Bank, Reliance, Tata Consumer Products, TCS), 4 RBI/SEBI regulatory documents, 2 IRDAI circulars and the NISM Series XV Research Analyst workbook. File list and sources: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

**Build phases (0 to 12):** Scaffold & Spec; Project Setup & MLOps; Document Ingestion; Embeddings & Vector Store; Retrieval System; LLM Generator; Chat UI (Streamlit, since replaced by the FastAPI-served web UI); Containerization; Corpus Ops; Confidence Gate + Metadata Propagation; Hardening, Resume Unification, Cleanup; Evaluation, Hybrid Default, Cleanup; Evaluation Fixes and Documentation. Details: [docs/PHASE_LOG.md](docs/PHASE_LOG.md).

## Evaluation

Retrieval (`data/eval_questions.json`, 10 questions; `python scripts/eval_retrieval.py`; benchmark `python scripts/eval_rag_metrics.py` writes [reports/EVALUATION_BENCHMARK.md](reports/EVALUATION_BENCHMARK.md)). Target: 70% retrieval hit rate or better.

| Metric (top-5, n=10) | Dense | Hybrid (BM25 + RRF) |
| :--- | :---: | :---: |
| Hit rate | 100.0% (10/10) | 100.0% (10/10) |
| MRR | 0.678 | 0.703 |
| Precision@5 | 0.520 | 0.460 |
| P95 latency (local CPU, warm) | 52.3 ms | 42.4 ms |

Answer quality (`python scripts/eval_ragas.py` and `python scripts/eval_ragas.py --hybrid`; report [reports/RAGAS_EVAL.md](reports/RAGAS_EVAL.md), also shown in the app via `GET /eval`). Generator `openai/gpt-oss-20b` (paid endpoint, no fallbacks); judge `deepseek/deepseek-v4.1-flash` via OpenRouter with local MiniLM embeddings; RAGAS 0.4.3. Methodology and failure analysis: [docs/EVALUATIONS.md](docs/EVALUATIONS.md).

| Metric (mean, n=10) | Dense | Hybrid (BM25 + RRF) |
| :--- | :---: | :---: |
| Faithfulness | 0.744 | 0.788 |
| Response relevancy | 0.509 | 0.541 |
| Context precision (no reference) | 0.470 | 0.287 |
| NaN scores / generation failures | 0 / 0 | 0 / 0 |

Caveats:

- Small sample: with n=10, one question moves a mean by 0.1, so differences between dense and hybrid are not statistically meaningful.
- The judge is a single LLM and is noisy. Response relevancy is computed from 1 generated question per answer, not 3, because OpenRouter ignores the `n` parameter.
- The retrieval eval uses wide `expected_page` ranges (for example 1 to 500 for the annual report), so its hit rate is lenient: `kyc-001` counts as a hit although the retrieved chunks do not contain the identification-document list.
- Refusals ("the context does not contain...") score 0 on response relevancy by RAGAS design. Eight of the 20 answers did (four per mode).
- Lowest-faithfulness answers have two causes (see docs/EVALUATIONS.md): the generator stated figures or steps that are not in the retrieved text (`hdfc-002`, `aml-002`), or retrieval returned the right document but not the needed passage (`kyc-001`, `capital-001`).
- The RAGAS runs use `openai/gpt-oss-20b`. The live deployment uses the default `openrouter/free` model, so these scores describe the pipeline with the eval generator, not the live model.
- Free-tier generation (`openrouter/free`) was tried first and rejected for evaluation: 1/10 (dense) and 5/10 (hybrid) answers were generation failures, so those runs are not reported.
- The eval set was corrected on 2026-10-03: three questions pointed at PDFs that were never in the corpus and now point at documents that are. Earlier numbers are not comparable.

## Known limitations

- No OCR: scanned PDFs are not supported.
- Low confidence is only a flag: when the best retrieval distance is above `LOW_CONFIDENCE_DISTANCE`, the answer is still generated and returned with `low_confidence: true`. It is not a gate.
- If the LLM call fails (after retries and any fallback models) or the API key is missing, `/ask` returns HTTP 200 with the text "I could not generate a reliable answer right now. Please try again." and no citations.
- Failover is OpenRouter retries (default 3 per model) plus the optional `OPENROUTER_FALLBACK_MODELS` list, which is empty by default. There is no gateway-level failover.
- Portkey is not used: `PORTKEY_API_KEY` and `PORTKEY_GATEWAY_URL` are defined in `configs/settings.py` but never read. The same is true of `HYBRID_ALPHA` (the RRF weight is hard-coded to 0.5 in `src/retriever.py`), `LLM_PROVIDER`, `ENVIRONMENT` and `LOG_LEVEL`.
- `src/rag_pipeline.py` (`ask_question`) retrieves with dense search only; hybrid applies through the API (`/ask`) and the evaluation scripts.
- Evaluation limits: n=10, a single LLM judge, wide page ranges, no reference answers, and the eval generator differs from production. See [docs/EVALUATIONS.md](docs/EVALUATIONS.md).
- Generated reports are not hand-edited, so these known issues remain in them: `reports/EVALUATION_BENCHMARK.md` lists "Latency (P50/P95)" in its header but reports average and P95 only, and says RRF "balances precision and semantic recall" while hybrid Precision@5 is lower (0.460 vs 0.520).
- The UI model badge falls back to the label `Portkey / MiniLM` when a response has no `model` value (`api/index.html:412`), although Portkey is not used.
- The rate limit is in memory and per instance, so it is not shared across Cloud Run instances.
- There is no authentication beyond the optional `API_KEY` header, and only `/ask` is protected.
- Production runs the free-tier `openrouter/free` model, which is less reliable than the paid model used for evaluation.
- A push to `main` redeploys Cloud Run unless it only changes `docs/**` or `*.md` files (`paths-ignore` in `deploy.yml`), so a docs-only merge does not redeploy. Manual runs (`workflow_dispatch`) still deploy. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Possible improvements (not implemented): OCR for scanned PDFs, multi-collection routing, reference answers for Context Recall and answer-correctness scoring, a larger eval set, scheduled evaluation runs.

## Documentation

- [docs/README.md](docs/README.md): index of all documents
- [docs/DECISIONS.md](docs/DECISIONS.md): architecture decision records
- [CHANGELOG.md](CHANGELOG.md): what changed
- [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md), [docs/API.md](docs/API.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/EVALUATIONS.md](docs/EVALUATIONS.md)

## License

MIT, see [LICENSE](LICENSE).
