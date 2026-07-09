# Retrieval Evaluation Report

Run `python scripts/eval_retrieval.py` to regenerate this report.

## Methodology
- **Eval set:** `data/eval_questions.json` (10 compliance questions)
- **Metric:** Retrieval hit rate — expected document appears in top-5 results with page in expected range
- **Target:** ≥ 70% hit rate

## Latest Results
- **Hit rate:** 90.0% (9/10) — see `reports/retrieval_eval.json`
- **Chunk count:** 3459
- **Corpus:** varies by local `data/raw_pdfs/` contents at index-build time

## Notes
- Eval measures **retrieval quality**, not LLM answer quality
- Empty vector store returns 0% — run `python scripts/build_index.py` first
- Track corpus size using `/health` and `data/chroma_db/index_meta.json` after each rebuild

## Interview Framing
Report hit rate honestly. If a question misses, explain whether chunking, corpus gap, or query phrasing caused it.
