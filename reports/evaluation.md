# Retrieval Evaluation Report

Run `python scripts/eval_retrieval.py` to regenerate this report.

## Methodology
- **Eval set:** `data/eval_questions.json` (10 compliance questions)
- **Metric:** Retrieval hit rate — expected document appears in top-5 results with page in expected range
- **Target:** ≥ 70% hit rate

## Latest Results
- **Hit rate (dense):** 70.0% (7/10) — see `reports/retrieval_eval.json`
- **Chunk count:** 12075
- **Corpus:** varies by local `data/raw_pdfs/` contents at index-build time

## Notes
- Eval measures **retrieval quality**, not LLM answer quality; see [RAGAS_EVAL.md](RAGAS_EVAL.md) for answer quality and [EVALUATION_BENCHMARK.md](EVALUATION_BENCHMARK.md) for dense vs hybrid
- Empty vector store returns 0% — run `python scripts/build_index.py` first
- Track corpus size using `/health` and `data/chroma_db/index_meta.json` after each rebuild

## Interview Framing
Report hit rate honestly. If a question misses, explain whether chunking, corpus gap, or query phrasing caused it.
