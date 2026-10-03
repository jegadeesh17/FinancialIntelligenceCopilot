# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). No versions have been released; everything is listed under Unreleased and is built from the repository's `feat`, `fix` and `refactor` commits.

## [Unreleased]

### Added

- Project scaffold with spec, docs and checkpoint tests, then PDF ingestion with chunking and a download script (`66741e7`).
- Local embeddings and a persistent ChromaDB vector store (`023d466`).
- Semantic top-k retriever (`f5cf1be`).
- OpenRouter answer generator with page-level citations (`31c5a57`).
- Streamlit chat UI wired to the RAG pipeline (`070b53a`; removed later, see Changed), Docker deployment and container tests (`7239e19`).
- Trust UX, ops controls and audit logging (`51df51e`).
- Rebrand to Financial Intelligence Copilot, with chunk metadata and a low-confidence distance threshold (`121ea23`).
- Hybrid BM25 + dense retrieval, pydantic-settings configuration and a retrieval benchmark (`ce70e4e`).
- Web UI served by FastAPI at `/app` and a GitHub Actions workflow that deploys to GCP Cloud Run (`2ccac45`).
- RAGAS answer-quality evaluation script and reports (`dad3a7f`).
- `GET /eval` endpoint exposing the evaluation summary (`1da771f`).
- "Eval metrics" popover and a one-screen hero layout in the web UI (`117bec1`).
- MIT `LICENSE`, deployment and API docs (`204a6f3`), and evaluation methodology and decision records in `docs/EVALUATIONS.md` and `docs/DECISIONS.md` (`90b7652`).

### Changed

- Hardened generation reliability with fallback models and retries, and removed non-core scraping features (`b43475e`).
- Hybrid search is now the default for `/ask`, docker-compose ports match the container, and unhandled errors return a sanitized body (`558e0dc`).
- Removed the Streamlit UI; the FastAPI-served web UI is the only UI (`dbf2049`).
- Split `requirements-dev.txt` (pytest, RAGAS) from `requirements.txt` so the production image stays lean (`117d3fb`).
- Documentation refresh: standard README section order, docs index, changelog, commented `.env.example`, expanded `.gitignore`; corrected claims about the benchmark numbers, test counts, corpus, chunking, hybrid fusion, confidence flag, LLM failure behaviour and unused settings (Portkey, `HYBRID_ALPHA`, `LLM_PROVIDER`, `ENVIRONMENT`, `LOG_LEVEL`); moved `reports/evaluation.md` out of version control.

### Fixed

- Pinned the Python 3.11 runtime and updated dependency versions for Streamlit Cloud (`9ac1fdd`, `d431930`).
- Streamlit Cloud index extraction and chat UI layout bugs (`f1d6455`, `2590d5c`, `9bc2a85`, `b9c6667`); the Streamlit deployment has since been replaced.
- Cloud Run deploy: removed the reserved `PORT` variable, standardized the Dockerfile venv and `PYTHONPATH`, baked the ChromaDB index and embedding model into the image, used the correct release asset name and created the Hugging Face cache directory with the right owner (`daee242`, `0fb1b66`, `d2df6ed`, `30db98d`, `8874fa1`).
- Latency benchmark now warms up the model before timing and report claims were corrected (`3b3b083`).
- Benchmark report prints the expected document instead of the question text and no longer cites a missing standards file (`f151916`).
- Evaluation questions `aml-001`, `aml-002` and `lodr-001` now point at PDFs that are in the corpus (`5f6a39d`).
