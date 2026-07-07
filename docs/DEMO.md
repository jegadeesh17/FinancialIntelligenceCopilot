# Financial Compliance RAG — 5-Minute Demo Script

## Prerequisites
```powershell
cd FinancialComplianceRAG
pip install -r requirements.txt
cp .env.example .env   # set OPENROUTER_API_KEY
python scripts/download_docs.py
python scripts/seed_extra_pdfs.py
python scripts/build_index.py
```

## Demo Flow (5 minutes)

### 1. Show retrieval evaluation (30 sec)
```powershell
python scripts/eval_retrieval.py
```
Point out hit rate ≥ 70% and `reports/retrieval_eval.json`.

### 2. Streamlit chat with citations (2 min)
```powershell
streamlit run app/app.py
```
Ask these three questions:
1. *"What KYC documents are required for individual customers?"*
2. *"What was HDFC Bank net interest income?"*
3. *"What disclosure obligations apply under SEBI LODR?"*

Show that each answer includes **Sources: filename (p.X)**.

### 3. FastAPI endpoint (1 min)
```powershell
uvicorn api.main:app --port 8000
```
In another terminal:
```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"What are AML customer due diligence requirements?\"}"
```

### 4. Architecture talking points (1 min)
- PDF ingest → chunk → embed → ChromaDB → retrieve → OpenRouter generate
- Pydantic settings, pytest checkpoints, citation guardrails
- Production-style MVP on laptop hardware (CPU embeddings)

## Interview Close
*"Compliance teams drown in regulatory PDFs. I built an auditable RAG system with page-level citations and measured retrieval quality on a 10-question eval set."*
