# Retrieval Evaluation Report

Run `python scripts/eval_retrieval.py` to regenerate this report.

## Methodology
- **Eval set:** `data/eval_questions.json` (10 questions across KYC/AML, capital adequacy, HDFC figures and SEBI disclosure/LODR)
- **Metric:** Retrieval hit rate — expected document appears in top-5 results with page in expected range
- **Target:** ≥ 70% hit rate

## Latest Results
- **Hit rate (dense):** 100.0% (10/10) — see `reports/retrieval_eval.json`
- **Chunk count:** 12075
- **Corpus:** varies by local `data/raw_pdfs/` contents at index-build time
- **Eval-set correction (2026-10-03):** `aml-001`, `aml-002` and `lodr-001` were re-pointed to PDFs that exist in the corpus (they previously expected files that were never indexed), so earlier hit rates are not comparable.

## Notes
- Eval measures **retrieval quality**, not LLM answer quality; see [RAGAS_EVAL.md](RAGAS_EVAL.md) for answer quality and [EVALUATION_BENCHMARK.md](EVALUATION_BENCHMARK.md) for dense vs hybrid
- Full methodology, results and failure analysis: [../docs/EVALUATIONS.md](../docs/EVALUATIONS.md)
- Empty vector store returns 0% — run `python scripts/build_index.py` first
- Track corpus size using `/health` and `data/chroma_db/index_meta.json` after each rebuild

## Interview Framing
Report hit rate honestly. If a question misses, explain whether chunking, corpus gap, or query phrasing caused it.
