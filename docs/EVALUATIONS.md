# Evaluations — Financial Intelligence Copilot

How the project measures retrieval quality and answer quality, how to re-run it, how to read the scores, and what the numbers do not prove. Design rationale lives in [DECISIONS.md](./DECISIONS.md); per-phase history in [PHASE_LOG.md](./PHASE_LOG.md).

---

## 1. Purpose and two layers

A RAG system can fail in two places, so there are two layers of evaluation:

| Layer | Question it answers | Scripts | Needs an LLM? |
| :--- | :--- | :--- | :---: |
| **1. Retrieval** | Did the retriever return the right document and page? | `scripts/eval_retrieval.py`, `scripts/eval_rag_metrics.py` | No |
| **2. Answer quality (RAGAS)** | Is the generated answer grounded in the retrieved text, and does it address the question? | `scripts/eval_ragas.py` | Yes (generator + judge) |

Layer 1 can pass while layer 2 fails: the right page can be retrieved and the generator can still misread it (see section 8).

---

## 2. Eval set

`data/eval_questions.json` holds **10 questions**. Each entry has `id`, `question`, `expected_doc` (a substring matched against the chunk's source file name), `expected_page_min` and `expected_page_max`.

| Topic | Question ids | Expected document |
| :--- | :--- | :--- |
| KYC | `kyc-001`, `kyc-002` | `rbi_master_direction_kyc` (pages 1–30) |
| AML / CFT | `aml-001`, `aml-002` | `rbi_master_direction_kyc` (pages 1–75 and 1–50) |
| Capital adequacy and HDFC figures | `capital-001`, `hdfc-001`, `hdfc-002` | `HDFC_Bank_Annual_Report` (pages 1–500) |
| SEBI disclosure | `sebi-001`, `sebi-002` | `sebi_circular_disclosure` (pages 1–20) |
| SEBI LODR governance | `lodr-001` | `sebi_lodr_ncd_operational_circular` (pages 1–75) |

Page ranges are deliberately wide, so a "hit" means the right document and a roughly right region, not the exact page.

> **History note (2026-10-03).** `aml-001`, `aml-002` and `lodr-001` originally expected `rbi_master_direction_aml` and `sebi_lodr_governance`. Neither file was ever in `data/raw_pdfs/` (both were only optional entries in `scripts/download_docs.py`, since removed, and neither is in the finalized 12-PDF corpus), so those three questions could never hit, and `aml-002` was answered from model memory. They now point at documents that exist (the RBI KYC Master Direction covers AML/CFT and customer due diligence; the SEBI LODR NCD operational circular is the closest LODR document in the corpus and mentions corporate governance on pages 3, 42 and 44, but it is about debt securities, so `lodr-001` is a weaker match than the others). Question text and ids are unchanged. **Results from before this date are not comparable.**

---

## 3. Layer 1 — Retrieval

- `scripts/eval_retrieval.py` — dense retrieval only. Writes `reports/retrieval_eval.json`.
- `scripts/eval_rag_metrics.py` — dense vs hybrid (BM25 + dense with RRF). Writes `reports/rag_benchmark.json` and `reports/EVALUATION_BENCHMARK.md`.

Definitions (top-k = 5):

| Metric | Definition |
| :--- | :--- |
| **Hit@5** | Share of questions where at least one of the top 5 chunks comes from the expected document **and** a page inside the expected range. |
| **MRR** | Mean of `1 / rank` of the first matching chunk (0 if none). |
| **Precision@5** | Matching chunks in the top 5, divided by 5, averaged over questions. |
| **Latency** | Wall time of `retrieve()` per question. One warm-up call per mode is made first, so embedding-model load is not counted. Reported as mean and P95. |

---

## 4. Layer 2 — RAGAS answer quality

`scripts/eval_ragas.py` asks each question through the real pipeline (`retrieve` then generate), then scores the answer with [RAGAS](https://docs.ragas.io) 0.4.3.

**Metrics** (all reference-free):

| Metric | What it measures |
| :--- | :--- |
| **Faithfulness** | Share of claims in the answer that are supported by the retrieved chunks. |
| **Response relevancy** | Similarity between the question and questions regenerated from the answer. RAGAS scores a **noncommittal answer (a refusal) as 0**. |
| **Context precision (without reference)** | Rank-weighted share of the retrieved chunks that the judge finds useful for answering. |

**Why no Context Recall:** it needs a reference answer per question, and the eval set has none.

**Setup**

- **Separate judge.** The generator (`openai/gpt-oss-20b`) and the judge (`deepseek/deepseek-v4.1-flash`, `DEFAULT_JUDGE_MODEL`) are different models, so the generator does not grade itself. Override the judge with `--judge-model`.
- **Judge cost cap.** `JUDGE_PROVIDER_ROUTING` asks OpenRouter to route the judge by price with a maximum price of 0.15 (prompt) and 0.60 (completion) USD per million tokens.
- **Local embeddings.** `MiniLMRagasEmbeddings` reuses the local MiniLM model, so RAGAS makes no paid embedding calls.
- **Run config.** `RunConfig(max_workers=4, timeout=180)`. Lower `--max-workers` if OpenRouter rate-limits.
- **NaN policy.** A metric that fails to score is NaN. NaNs are excluded from the means, kept in the per-question tables, and counted in `nan_counts`.
- **Generation failures.** An answer equal to `GENERATION_FAILED_TEXT` is flagged `generation_failed` and counted in `generation_failures`, so a pipeline outage is not mistaken for a low score.
- **Pins.** `requirements-dev.txt` pins `ragas==0.4.3` and `langchain-openai==1.1.9`. It also pins `langchain-community==0.3.31` because RAGAS 0.4.3 imports `langchain_community.chat_models.vertexai`, which was removed in langchain-community 0.4. These packages are not in the production image.

---

## 5. Eval generator vs production generator

The RAGAS runs use `OPENROUTER_MODEL=openai/gpt-oss-20b` with no fallbacks. **Production does not.** The deploy workflow sets only `OPENROUTER_API_KEY` on Cloud Run, so production uses the default `openrouter/free`.

The free tier was rejected for evaluation because of generation failures: in the first attempt, 1/10 dense and 5/10 hybrid answers failed (PHASE_LOG, Phase 11). Those runs were not reported.

So the RAGAS scores describe **this pipeline with `gpt-oss-20b`**, not the live free-tier model. Retrieval numbers (layer 1) do not depend on the generator and apply to production.

---

## 6. How to run

```bash
pip install -r requirements-dev.txt

python scripts/eval_retrieval.py                      # -> reports/retrieval_eval.json
python scripts/eval_rag_metrics.py                    # -> reports/rag_benchmark.json, reports/EVALUATION_BENCHMARK.md
OPENROUTER_MODEL=openai/gpt-oss-20b OPENROUTER_FALLBACK_MODELS= python scripts/eval_ragas.py
OPENROUTER_MODEL=openai/gpt-oss-20b OPENROUTER_FALLBACK_MODELS= python scripts/eval_ragas.py --hybrid
```

- Needs a built index (`python scripts/build_index.py`) and `OPENROUTER_API_KEY` in your local environment file (see `.env.example`).
- The two RAGAS runs call paid OpenRouter models. Each took about 4–5 minutes for 10 questions.
- Outputs go to `reports/`. The live UI **Eval metrics** popover (`GET /eval`) shows whatever is committed in `reports/` at deploy time.
- Each RAGAS run replaces its own mode (`dense` or `hybrid`) inside `reports/ragas_eval.json`.

---

## 7. Latest results (2026-10-03)

Corpus: 12,075 chunks. Eval set: 10 questions. Top-k: 5.

**Retrieval** (source: `reports/rag_benchmark.json`; the dense hit rate also matches `reports/retrieval_eval.json`)

| Metric | Dense | Hybrid |
| :--- | :---: | :---: |
| Hit@5 | 100.0% (10/10) | 100.0% (10/10) |
| MRR | 0.6783 | 0.7033 |
| Precision@5 | 0.5200 | 0.4600 |
| Avg latency (warm) | 43.66 ms | 37.72 ms |
| P95 latency (warm) | 52.28 ms | 42.44 ms |

Latency differences between runs of the same code are noise at this scale; do not read the hybrid latency as a speed-up.

**Answer quality — RAGAS** (source: `reports/ragas_eval.json`; generator `openai/gpt-oss-20b`, judge `deepseek/deepseek-v4.1-flash`, RAGAS 0.4.3)

| Metric | Dense | Hybrid |
| :--- | :---: | :---: |
| Faithfulness | 0.7444 | 0.7882 |
| Response relevancy | 0.5089 | 0.5413 |
| Context precision (no reference) | 0.4700 | 0.2867 |
| NaN scores (per metric) | 0 | 0 |
| Generation failures | 0 | 0 |

Per-question scores, answers and retrieved-context counts are in `reports/RAGAS_EVAL.md` and `reports/ragas_eval.json`; the retrieval diagnostic per question is in `reports/EVALUATION_BENCHMARK.md`.

---

## 8. How to read the scores

**Response relevancy of 0.0 is a refusal.** Eight answers scored 0.0, four per mode, and every one is a "the provided context does not contain…" refusal:

- Dense: `kyc-001`, `kyc-002`, `capital-001`, `hdfc-001`.
- Hybrid: `kyc-001`, `capital-001`, `hdfc-001`, `hdfc-002`.

The metric therefore penalises correct abstention. Faithfulness moves the other way: refusals tend to score high on it (for example the hybrid refusals on `capital-001`, `hdfc-001` and `hdfc-002` score 1.0). A mean of either metric mixes "answered well" with "declined". As a derived figure (not a RAGAS output, computed from `per_question` in `reports/ragas_eval.json`), the mean relevancy over the 6 non-refused answers is 0.8481 for dense and 0.9021 for hybrid.

**Dense vs hybrid answer rate.** Both modes answered 6 of 10 questions and refused 4, but not the same ones. Dense answered `hdfc-002` (faithfulness 0.43, see below) and refused `kyc-002`. Hybrid answered `kyc-002` (faithfulness 0.90, relevancy 1.00) and refused `hdfc-002`. Hybrid's higher mean faithfulness is largely that swap, and with n=10 one question moves a mean by 0.1.

**Context precision is lower for hybrid (0.2867 vs 0.4700).** In the two AML questions I inspected, the hybrid top 5 contained off-topic chunks (an HDFC annual-report chunk and a NISM workbook chunk for `aml-002`; four non-KYC chunks, three HDFC and one IRDAI, for `aml-001`). That is consistent with BM25 pulling in keyword matches, but I did not test it across all ten questions.

**Hit@5 is lenient.** `kyc-001` counts as a hit in both modes (right document, page in range), yet its retrieved chunks contain none of the identification-document terms I searched for (officially valid document, Aadhaar, passport, driving licence, voter, proof of identity/address), and the answer is a refusal. A hit means "right document and region", not "the needed passage".

### Failure analysis

The three lowest-faithfulness questions per mode (dense has a tie at 0.50, so four are listed). Method: for each, I re-ran `retrieve(question, hybrid=...)`, then checked whether the numbers and terms in the answer appear in the retrieved chunk text and read the chunk openings. This is a targeted check, **not a claim-by-claim audit** of the judge's verdicts.

| Mode | Question | Faithfulness | Primary cause | Evidence |
| :--- | :--- | :---: | :--- | :--- |
| Dense | `hdfc-002` | 0.43 | **Prompt / generator** | The retrieved chunk from page 447 contains the deposits schedule (for example demand deposits "From others" 307,274.93). The answer states ₹307.78 cr → ₹311.42 cr, ₹598.74 cr → ₹630.47 cr and a total rise of ₹35.4 crore (+5.8%). None of those figures appear in the chunks. The generator misread the table and stated numbers anyway. |
| Dense | `aml-002` | 0.43 | **Prompt / generator** (retrieval contributes) | The retrieved RBI chunks cover third-party reliance, the Rs 50,000 transaction threshold, FATF enhanced due diligence and the PML Act framework. The answer's generic steps (customer identification, verification, risk assessment, record-keeping) are not in those chunks, so the generator filled in from background knowledge despite the grounding instruction. The core CDD procedure sections were not retrieved, and one top-5 chunk is from the HDFC report. |
| Dense | `kyc-001` | 0.50 | **Retrieval** (judge contributes) | Zero identification-document terms in the 5 chunks; the answer correctly refuses. A 0.50 faithfulness for a pure refusal is a judge artifact. |
| Dense | `capital-001` | 0.50 | **Retrieval** (judge contributes) | The chunks mention "capital adequacy ratio" only in notes about how capital funds are computed, with no ratio figure. Rank 1 is a TCS chunk. The answer correctly refuses. |
| Hybrid | `aml-002` | 0.31 | **Prompt / generator** (retrieval contributes) | Same pattern as dense: the answer's generic CDD steps are not in the chunks, and the top 5 include an HDFC chunk (page 236) and a NISM workbook chunk (page 267). |
| Hybrid | `kyc-001` | 0.50 | **Retrieval** (judge contributes) | Same as dense. |
| Hybrid | `aml-001` | 0.62 | **Judge** (probable) | The policy elements the answer lists (customer acceptance, identification, risk management, transaction monitoring, annual review, branches abroad applying the more stringent standard) all appear in the retrieved text, so the low score is probably the judge. Only 1 of the 5 chunks is from the KYC direction, and I confirmed this by keyword match only, not by reading each claim. |

Takeaways: the two most damaging errors are the generator stating figures or steps the context does not contain (`hdfc-002`, `aml-002`), which retrieval metrics cannot see. The remaining low scores are retrieval gaps (the right document, the wrong passage) that the wide page ranges hide.

---

## 9. Limitations

- **n=10.** One question moves a mean by 0.1. Dense-vs-hybrid differences are not statistically meaningful.
- **One noisy LLM judge.** No second judge or human labels; judge errors are visible (for example 0.50 faithfulness for a refusal).
- **Relevancy uses 1 generated question per answer, not 3.** OpenRouter ignores the `n` parameter, and RAGAS logs "LLM returned 1 generations instead of requested 3".
- **Wide page ranges** make Hit@5 lenient (up to 1–500 for the annual report).
- **No reference answers**, so correctness and recall are not measured; only groundedness, relevance and context usefulness.
- **The eval generator is not the production generator** (section 5).
- **Results depend on the corpus** of 12 PDFs and on the chunking and embedding settings; they do not generalise to other documents.
- **Evals run manually, not in CI**, because they cost paid credits and need network access. Committed numbers can go stale after a code change.

---

## 10. Next steps

- Write reference answers for the eval set, which enables Context Recall and an answer-correctness check.
- Grow the eval set well beyond 10 questions, with a spread of question types (numeric lookup, multi-hop, out-of-corpus).
- Tighten the expected page ranges so Hit@5 means "the right passage".
- Run the evals on a schedule and record the history, instead of keeping only the latest run.
