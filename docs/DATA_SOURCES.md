# PDF Data Sources — Financial Intelligence Copilot

All PDFs are stored manually in `data/raw_pdfs/` (gitignored). **Only use real PDFs from official sites.**

## Workflow

```bash
# 1) Add PDFs manually to data/raw_pdfs/
# 2) Build Chroma index
python scripts/build_index.py

# 3) Run UI
streamlit run app/app.py
```

---

## Finalized corpus (12 PDFs)

### Annual reports (5)

| Filename | Company |
|----------|---------|
| `hdfc_bank_annual_report.pdf` | HDFC Bank |
| `icici_bank_annual_report.pdf` | ICICI Bank |
| `RIL-Integrated-Annual-Report-2025-26.pdf` | Reliance Industries |
| `Tata Consumer Products Ltd IAR 2025-2026.pdf` | Tata Consumer Products |
| `tcs_annual_report.pdf` | TCS |

### Regulatory — RBI + SEBI (4)

| Filename | Source |
|----------|--------|
| `rbi_master_direction_kyc.pdf` | RBI — KYC / AML/CFT Master Direction |
| `rbi_master_direction_fraud_reporting.pdf` | RBI — Fraud classification & reporting |
| `sebi_circular_disclosure.pdf` | SEBI — integrated reporting / BRR disclosure |
| `sebi_lodr_ncd_operational_circular.pdf` | SEBI — LODR for NCD / securitized debt |

### Insurance — IRDAI (2)

| Filename | Source |
|----------|--------|
| `irdai_life_insurance_products.pdf` | IRDAI — life insurance products master circular |
| `irdai_investment_master_circular.pdf` | IRDAI — investment master circular |

### Exam reference (1)

| Filename | Source |
|----------|--------|
| `nism_research_analyst_workbook.pdf` | NISM Series XV Research Analyst workbook |

---

## Requirements

- Text-selectable PDFs (copy/paste works)
- English, publicly available
- No automated PDF seeding scripts
