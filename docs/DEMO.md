# Demo — Financial Intelligence Copilot

## Setup

```powershell
cd FinancialIntelligenceCopilot
pip install -r requirements.txt
# .env must contain OPENROUTER_API_KEY

python scripts/build_index.py
uvicorn api.main:app --port 8000   # then open http://localhost:8000/app
```

Live deployment: [https://financial-copilot-api-242711953247.asia-south1.run.app/app](https://financial-copilot-api-242711953247.asia-south1.run.app/app)

Add PDFs manually to `data/raw_pdfs/` — see [DATA_SOURCES.md](DATA_SOURCES.md).

## 5-minute demo flow

1. **Status chip** — show the indexed chunk count (top right) and the hybrid BM25 + dense toggle.
2. **Regulatory question** — *"What are RBI KYC requirements for individual customers?"*
3. **Annual report question** — *"What was HDFC Bank net interest income?"*
4. **Exam reference question** — *"What are research analyst conflict-of-interest rules?"*
5. **Citations** — show the source documents and pages under each answer.
6. **Quality metrics** — click **Eval metrics** (top right) to show RAGAS faithfulness / relevancy / context precision and retrieval hit rate for dense vs hybrid. Talking points (why a separate judge, why no ContextRecall, why refusals score 0): [EVALUATIONS.md](EVALUATIONS.md).

## Rebuild index after PDF changes

```powershell
python scripts/build_index.py
```
