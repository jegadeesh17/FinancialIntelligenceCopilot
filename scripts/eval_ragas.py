"""
RAGAS Answer-Quality Evaluation — Dense vs. Hybrid BM25 Retrieval.

Computes (LLM-judged, no reference answers required):
- Faithfulness
- Response Relevancy
- Context Precision (without reference)

Generator: src/generator.py (OpenRouter). Judge: a different OpenRouter model.
Writes results to: reports/RAGAS_EVAL.md and reports/ragas_eval.json
"""

from __future__ import annotations

import json
import math
import sys
import time
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval_questions.json"
REPORT_MD_PATH = PROJECT_ROOT / "reports" / "RAGAS_EVAL.md"
REPORT_JSON_PATH = PROJECT_ROOT / "reports" / "ragas_eval.json"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_JUDGE_MODEL = "deepseek/deepseek-v4.1-flash"
# OpenRouter provider routing: refuse providers priced above DeepSeek's official rate (USD per 1M tokens).
JUDGE_PROVIDER_ROUTING = {"sort": "price", "max_price": {"prompt": 0.15, "completion": 0.60}}
GENERATION_FAILED_TEXT = "I could not generate a reliable answer right now. Please try again."

sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings("ignore", category=DeprecationWarning)

import ragas  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from ragas import EvaluationDataset, RunConfig, SingleTurnSample, evaluate  # noqa: E402
from ragas.embeddings import BaseRagasEmbeddings  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import (  # noqa: E402
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
)

from configs.settings import get_settings  # noqa: E402
from src.embeddings import embed_query, embed_texts  # noqa: E402
from src.generator import generate_answer  # noqa: E402
from src.retriever import retrieve  # noqa: E402

METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Response Relevancy",
    "llm_context_precision_without_reference": "Context Precision",
}


class MiniLMRagasEmbeddings(BaseRagasEmbeddings):
    """Expose the project's sentence-transformers MiniLM model to RAGAS."""

    def embed_query(self, text: str) -> list[float]:
        return embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)


def _nan_to_none(value: object) -> float | None:
    if value is None:
        return None
    number = float(value)
    return None if math.isnan(number) else round(number, 4)


def build_judge_llm(judge_model: str, api_key: str) -> tuple[ChatOpenAI, LangchainLLMWrapper]:
    chat = ChatOpenAI(
        model=judge_model,
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        temperature=0,
        extra_body={"reasoning": {"enabled": False}, "provider": JUDGE_PROVIDER_ROUTING},
    )
    return chat, LangchainLLMWrapper(chat)


def run_ragas_eval(hybrid: bool, judge_model: str, max_workers: int) -> dict:
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Missing evaluation dataset: {EVAL_PATH}")

    settings = get_settings()
    if not settings.openrouter_api_key:
        return {"error": "OPENROUTER_API_KEY is not set in the environment."}
    if judge_model == settings.openrouter_model:
        return {"error": "Judge model must differ from the generator model."}

    questions = json.loads(EVAL_PATH.read_text(encoding="utf-8"))

    chat, judge_llm = build_judge_llm(judge_model, settings.openrouter_api_key)
    chat.invoke("Reply with OK")  # smoke test: fails fast on bad routing / unsupported fields

    samples: list[SingleTurnSample] = []
    details: list[dict] = []
    for item in questions:
        q = item["question"]
        contexts = retrieve(q, hybrid=hybrid)
        resp = generate_answer(q, contexts)
        samples.append(
            SingleTurnSample(
                user_input=q,
                response=resp.answer,
                retrieved_contexts=[c.text for c in contexts],
            )
        )
        details.append(
            {
                "id": item.get("id"),
                "question": q,
                "answer": resp.answer,
                "generator_model": resp.model,
                "generation_failed": resp.answer == GENERATION_FAILED_TEXT,
                "n_contexts": len(contexts),
            }
        )

    metrics = [Faithfulness(), ResponseRelevancy(), LLMContextPrecisionWithoutReference()]
    result = evaluate(
        EvaluationDataset(samples=samples),
        metrics=metrics,
        llm=judge_llm,
        embeddings=MiniLMRagasEmbeddings(),
        run_config=RunConfig(max_workers=max_workers, timeout=180),
        raise_exceptions=False,
    )
    df = result.to_pandas()

    metric_names = [m.name for m in metrics]
    means: dict[str, float | None] = {}
    nan_counts: dict[str, int] = {}
    n_scored: dict[str, int] = {}
    for name in metric_names:
        scores = [_nan_to_none(v) for v in df[name]]
        for detail, score in zip(details, scores):
            detail[name] = score
        valid = [s for s in scores if s is not None]
        nan_counts[name] = len(scores) - len(valid)
        n_scored[name] = len(valid)
        means[name] = round(sum(valid) / len(valid), 4) if valid else None

    return {
        "mode": "hybrid" if hybrid else "dense",
        "hybrid": hybrid,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generator_model_config": settings.openrouter_model,
        "generator_models_used": sorted({d["generator_model"] for d in details}),
        "judge_model": judge_model,
        "ragas_version": ragas.__version__,
        "n_questions": len(details),
        "generation_failures": sum(d["generation_failed"] for d in details),
        "nan_counts": nan_counts,
        "n_scored": n_scored,
        "means": means,
        "per_question": details,
    }


def _fmt(value: float | None) -> str:
    return "NaN" if value is None else f"{value:.4f}"


def generate_markdown_report(data: dict) -> str:
    runs = data["runs"]
    first = next(iter(runs.values()))
    generators = sorted({m for r in runs.values() for m in r["generator_models_used"]})
    judges = sorted({r["judge_model"] for r in runs.values()})

    md = f"""# RAGAS Answer-Quality Evaluation Report

> **Generator model**: `{first['generator_model_config']}` (resolved: {', '.join(f'`{g}`' for g in generators)})
> **Judge model**: {', '.join(f'`{j}`' for j in judges)}
> **RAGAS version**: `{first['ragas_version']}`
> **Questions**: `{first['n_questions']}`
> **Judge embeddings**: `all-MiniLM-L6-v2` (local)

---

## 1. Summary: Dense vs. Hybrid BM25 Retrieval

| Metric | Dense mean (NaN) | Hybrid mean (NaN) |
| :--- | :---: | :---: |
"""
    for name, label in METRIC_LABELS.items():
        cells = []
        for mode in ("dense", "hybrid"):
            run = runs.get(mode)
            cells.append("not run" if run is None else f"**{_fmt(run['means'][name])}** ({run['nan_counts'][name]} NaN)")
        md += f"| {label} | {cells[0]} | {cells[1]} |\n"

    for mode in ("dense", "hybrid"):
        run = runs.get(mode)
        if run is None:
            continue
        md += f"\n---\n\n## {'2' if mode == 'dense' else '3'}. Per-Question Scores: {mode.title()} (run {run['date']})\n\n"
        md += "| Query ID | Faithfulness | Response Relevancy | Context Precision | Generation failed |\n"
        md += "| :--- | :---: | :---: | :---: | :---: |\n"
        for d in run["per_question"]:
            scores = " | ".join(_fmt(d[name]) for name in METRIC_LABELS)
            md += f"| `{d['id']}` | {scores} | {'yes' if d['generation_failed'] else 'no'} |\n"

    md += "\n---\n*Report auto-generated by `scripts/eval_ragas.py`. NaN = the judge failed to produce a score; NaN rows are excluded from means, never dropped from the table.*\n"
    return md


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run RAGAS answer-quality evaluation.")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid BM25 + dense retrieval")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="OpenRouter judge model slug")
    parser.add_argument("--max-workers", type=int, default=4, help="RAGAS concurrency (lower if rate-limited)")
    args = parser.parse_args()

    mode = "hybrid" if args.hybrid else "dense"
    print(f"Running RAGAS evaluation ({mode}) with judge={args.judge_model}...")
    run = run_ragas_eval(args.hybrid, args.judge_model, args.max_workers)

    if "error" in run:
        print(f"Error: {run['error']}")
        return 1

    data = json.loads(REPORT_JSON_PATH.read_text(encoding="utf-8")) if REPORT_JSON_PATH.exists() else {}
    data.setdefault("runs", {})[mode] = run
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(generate_markdown_report(data), encoding="utf-8")

    print("RAGAS evaluation completed!")
    for name, label in METRIC_LABELS.items():
        print(f"- {label}: mean={_fmt(run['means'][name])} NaN={run['nan_counts'][name]}/{run['n_questions']}")
    print(f"- Generation failures: {run['generation_failures']}")
    print(f"- JSON results: {REPORT_JSON_PATH}")
    print(f"- Markdown report: {REPORT_MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
