# Retrieval Evaluation Report

Run `python scripts/eval_retrieval.py` to regenerate this report.

## Methodology
- **Eval set:** `data/eval_questions.json` (10 compliance questions)
- **Metric:** Retrieval hit rate — expected document appears in top-5 results with page in expected range
- **Target:** ≥ 70% hit rate

## Latest Results
- **Hit rate:** 90.0% (9/10) — see `reports/retrieval_eval.json`
- **Chunk count:** 3459
- **Corpus:** 5 PDFs (RBI KYC, HDFC annual report, SEBI circular, AML + LODR seeds)

## Notes
- Eval measures **retrieval quality**, not LLM answer quality
- Empty vector store returns 0% — run `python scripts/build_index.py` first
- Supplementary PDFs: `python scripts/seed_extra_pdfs.py`

## Interview Framing
Report hit rate honestly. If a question misses, explain whether chunking, corpus gap, or query phrasing caused it.
