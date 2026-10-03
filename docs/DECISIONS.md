# Architecture Decisions — Financial Intelligence Copilot

> Lightweight architecture decision records (ADRs). Per-phase notes are in [PHASE_LOG.md](./PHASE_LOG.md); the full specification is in [PROJECT_SPEC.md](./PROJECT_SPEC.md).

Rationale here is taken only from recorded sources (PHASE_LOG, PROJECT_SPEC, DEPLOYMENT, README, commit messages). Where no reason was recorded, the entry says so and lists only the observable trade-off.

---

## ADR-01: OpenRouter as LLM gateway with a fallback chain

**Context:** Answers must be generated from retrieved context with citations. PROJECT_SPEC section 2.2 lists local LLM inference as out of scope and calls OpenRouter "the locked provider".
**Decision:** Call LLMs through OpenRouter (`OPENROUTER_MODEL`, default `openrouter/free`), with an optional fallback model list (`OPENROUTER_FALLBACK_MODELS`) and retries (`LLM_MAX_RETRIES=3`). Commit b43475e added the fallback and retry handling to strengthen generation reliability. HTTP timeout is 15 s connect / 45 s read (NFR-04).
**Alternatives rejected:** Local LLM inference is out of scope (no reason recorded). No other gateway comparison is recorded.
**Consequences:** Generation depends on a third-party API and an `OPENROUTER_API_KEY` (passed to Cloud Run as an env var). The default `openrouter/free` model proved unreliable for evaluation (see ADR-10).

---

## ADR-02: MiniLM CPU embeddings (all-MiniLM-L6-v2)

**Context:** Embeddings are computed locally. NFR-03 requires that they run on CPU so the project works on 4GB VRAM laptops.
**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` on CPU (384-dimensional vectors), locked in the Scaffold phase. The Docker image bakes the model in (commit d2df6ed).
**Alternatives rejected:** None recorded.
**Consequences:** No GPU is needed and no embedding API is called. Model load time is real: latency benchmarking needed a warm-up call so model load is not counted (commit 3b3b083). The same local MiniLM embeddings are reused by the RAGAS evaluation (ADR-09).

---

## ADR-03: ChromaDB persistent store

**Context:** Chunk vectors and metadata (`source`, `page`, and later `source_url`, `regulator`, and so on) must survive between runs and be queryable by the retriever.
**Decision:** Use ChromaDB as a persistent local store (`data/chroma_db/`), locked in the Scaffold phase. Upserts are batched to respect Chroma's maximum batch size (PHASE_LOG, Phase 3).
**Alternatives rejected:** None recorded. No reason for choosing ChromaDB over other vector stores is recorded.
**Consequences:** The index is a directory of files, gitignored, so it must be rebuilt (`python scripts/build_index.py`) or shipped separately; see ADR-08. `chromadb>=1.5.9` is pinned in `requirements.txt`.

---

## ADR-04: Paragraph-aware chunking 800/100

**Context:** Chunks must keep meaning intact and carry `source` and 1-indexed `page` so every answer can cite document and page. FR-03 requires chunking that is "not naive char splits".
**Decision:** Split on `\n\n` first and hard-split only when a single paragraph exceeds `chunk_size`. Size and overlap are 800 / 100 characters (`CHUNK_SIZE`, `CHUNK_OVERLAP`); config validation requires `chunk_overlap` to stay smaller than `chunk_size`.
**Alternatives rejected:** Naive character splitting (FR-03). No reason is recorded for the specific values 800 and 100.
**Consequences:** Chunk boundaries follow paragraph structure in the extracted PDF text. Changing the sizes means re-embedding and rebuilding the index.

---

## ADR-05: Hybrid BM25 + dense with RRF, on by default

**Context:** Hybrid search was added in commit ce70e4e, but the API default was hardcoded to `False`, so it was never used unless a caller opted in.
**Decision:** Fuse dense vector results with BM25 (`rank-bm25`) via Reciprocal Rank Fusion, and default `AskRequest.hybrid` to `ENABLE_HYBRID_SEARCH` (true; `HYBRID_ALPHA=0.5`) "so hybrid ... is actually used unless a caller overrides it" (commit 558e0dc).
**Alternatives rejected:** Dense-only retrieval as the default (the previous behaviour; still selectable per request).
**Consequences:** In the latest run (n=10, top-5; see [EVALUATIONS.md](./EVALUATIONS.md)) both modes hit 10/10, hybrid has a slightly higher MRR (0.703 vs 0.678) and lower Precision@5 (0.46 vs 0.52), and P95 latency is 52.3 ms dense vs 42.4 ms hybrid, which is run-to-run noise rather than a hybrid speed-up. RAGAS shows faithfulness 0.744 vs 0.788, response relevancy 0.509 vs 0.541 and context precision 0.470 vs 0.287 (dense vs hybrid). With n=10 these differences are small and should not be read as significant.

---

## ADR-06: Low-confidence distance gate 0.85

**Context:** In regulated finance a weak retrieval should not look like a confident answer. PHASE_LOG Phase 9: "when retrieval quality is weak, communicate uncertainty explicitly".
**Decision:** Flag retrieval as low confidence when the best distance exceeds `LOW_CONFIDENCE_DISTANCE` (default 0.85). `low_confidence` and `best_score` are returned through the pipeline, `/ask`, and the web UI (FR-11, FR-12).
**Alternatives rejected:** None recorded. No reason is recorded for the value 0.85.
**Consequences:** The gate flags weak retrieval (FR-11 says "flag"); it is a distance threshold on retrieval only and does not check the generated answer. The threshold is configurable by env var.

---

## ADR-07: Static web UI on FastAPI replacing Streamlit

**Context:** The project first shipped a Streamlit chat UI (Phase 6) and later added a static web UI at `/app` served by FastAPI (commit 2ccac45). Both existed for a time, with Streamlit as an opt-in compose service (commit 558e0dc).
**Decision:** Remove the Streamlit UI (`app/`, `src/chat.py`, `src/ui_styles.py`, the Streamlit tests, the compose service). `api/index.html`, served by FastAPI, is the only UI (commit dbf2049, marked `refactor!`).
**Alternatives rejected:** Streamlit (removed). The commit records what was removed, not why.
**Consequences:** One UI and one runtime (uvicorn) to maintain. Streamlit-based `AppTest` coverage is gone; the Phase 6 checkpoint now points at `pytest tests/test_api.py`. Anyone relying on `streamlit run app/app.py` loses that entry point.

---

## ADR-08: Cloud Run with the index baked in from a release asset

**Context:** The service runs on GCP Cloud Run (`financial-copilot-api`, `asia-south1`), deployed by GitHub Actions. The index is large and gitignored; commit 62cc161 deleted a 91.5 MB index archive from the repo and blocked `*.zip`, `*.7z`, `*.tar.gz` and `*.gz` from future commits.
**Decision:** CI does not build the index. The deploy workflow downloads release asset `chroma_db_linux.zip` from release `v0.1.0-data`, unzips it into `data/`, and bakes it (and the Hugging Face model) into the image (commits d2df6ed, 30db98d). Cloud Run runs with 2Gi memory, 1 CPU, min 0 / max 2 instances (DEPLOYMENT.md).
**Alternatives rejected:** The earlier Streamlit Community Cloud setup, which extracted an LZMA-compressed index at startup (commit f1d6455), is superseded; the reason for the move is not recorded.
**Consequences:** Updating the index is manual: rebuild locally, re-zip as `chroma_db_linux.zip`, replace the release asset, then redeploy. A push to `main` rebuilds and redeploys production (no path filter), so a docs-only merge also redeploys. Min instances is 0; no cold-start measurement is recorded.

---

## ADR-09: RAGAS with a separate judge model and reference-free metrics

**Context:** Retrieval hit rate alone does not measure answer quality. The eval set (`data/eval_questions.json`, n=10) has no reference answers.
**Decision:** `scripts/eval_ragas.py` scores faithfulness, response relevancy and context precision (no reference), using a judge model (`deepseek/deepseek-v4.1-flash` via OpenRouter) that is distinct from the generator (`openai/gpt-oss-20b`), with local MiniLM embeddings. RAGAS is pinned to 0.4.3 and installed only from `requirements-dev.txt`.
**Alternatives rejected:** None recorded. No reason is recorded for using a judge separate from the generator, or for the choice of metrics beyond the absence of reference answers.
**Consequences:** README caveats: n=10 is a small sample, a single LLM judge is noisy, and response relevancy uses 1 generated question per answer, not 3, because OpenRouter ignores the `n` parameter. RAGAS 0.4.3 needs `langchain-community==0.3.31` because it imports a module removed in later versions (requirements-dev.txt comment).

---

## ADR-10: Paid fixed generator (openai/gpt-oss-20b) for evals instead of the production free-tier model

**Context:** The first RAGAS runs used the free `openrouter/free` generator (the production default per PROJECT_SPEC section 5).
**Decision:** Evaluate with one fixed paid model, `openai/gpt-oss-20b` (paid endpoint, no fallbacks), so every run uses the same generator.
**Alternatives rejected:** The free tier `openrouter/free`: 1/10 (dense) and 5/10 (hybrid) answers were generation failures scored 0.0, so those runs are not reported (PHASE_LOG Phase 11; README caveats).
**Consequences:** The reported RAGAS numbers describe `openai/gpt-oss-20b`, not the model production uses by default, and evaluation runs incur OpenRouter cost. The README reports 0 NaN scores and 0 generation failures for the final runs.

---

## ADR-11: requirements.txt / requirements-dev.txt split

**Context:** RAGAS and its LangChain dependencies are only needed for `scripts/eval_ragas.py`, and pytest only for tests.
**Decision:** `requirements.txt` is runtime only. `requirements-dev.txt` starts with `-r requirements.txt` and adds pytest and RAGAS. CI installs `requirements-dev.txt`; the Docker image installs only `requirements.txt` so "the production image stays lean" (PHASE_LOG Phase 11, commit 117d3fb).
**Alternatives rejected:** None recorded (the previous single-file layout is implied but no comparison is recorded).
**Consequences:** Local evaluation and tests need `pip install -r requirements-dev.txt`; the README quickstart notes this. The pinned RAGAS/LangChain set (ADR-09) stays out of the production image.
