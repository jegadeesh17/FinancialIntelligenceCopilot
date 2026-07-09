# Demo — Financial Intelligence Copilot

## Setup

```powershell
cd FinancialIntelligenceCopilot
pip install -r requirements.txt
# .env must contain OPENROUTER_API_KEY

python scripts/build_index.py
streamlit run app/app.py
```

Add PDFs manually to `data/raw_pdfs/` — see [DATA_SOURCES.md](DATA_SOURCES.md).

## 5-minute demo flow

1. **Corpus sidebar** — show 5 annual reports, 4 regulatory, 2 insurance, 1 exam workbook.
2. **Regulatory question** — *"What are RBI KYC requirements for individual customers?"*
3. **Annual report question** — *"What was HDFC Bank net interest income?"*
4. **Exam reference question** — *"What are research analyst conflict-of-interest rules?"*
5. **Citations** — expand debug panel to show retrieved chunks with document category.

## Rebuild index after PDF changes

```powershell
python scripts/build_index.py
```
