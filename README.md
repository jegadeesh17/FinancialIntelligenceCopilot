# Financial Compliance RAG
---
### **Project Overview**
Financial Compliance RAG is an enterprise Retrieval-Augmented Generation system for BFSI compliance document intelligence. It ingests regulatory PDFs (RBI, SEBI) and financial filings (10-K, annual reports), embeds them into ChromaDB, and answers analyst questions via OpenRouter with **mandatory page-level source citations**.

**Interview pitch:** *"Compliance teams drown in regulatory PDFs they can't search effectively. I built an enterprise RAG system that ingests RBI circulars and financial filings, stores embeddings in ChromaDB, and answers questions via OpenRouter with mandatory page-level citations — so every answer is auditable."*

**Repository:** [github.com/jegadeesh17/FinancialComplianceRAG](https://github.com/jegadeesh17/FinancialComplianceRAG)  
**Full specification:** [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)  
**Learning log:** [docs/PHASE_LOG.md](docs/PHASE_LOG.md)

---
### **Key Features**
- PDF ingestion with PyMuPDF and page-level metadata (Phase 2)
- Paragraph-aware semantic chunking (800 chars / 100 overlap)
- Local CPU embeddings (`all-MiniLM-L6-v2`) + ChromaDB vector store
- Top-k retrieval with source metadata
- OpenRouter LLM generation with strict context-only prompting
- Streamlit chat UI with citation display (doc name + page)
- Checkpoint tests per phase (`pytest tests/test_phaseN_*.py`)

---
### **Dataset**
- **Corpus:** Compliance-first mixed — ~40% regulatory circulars, ~40% annual reports/10-K, ~20% insurance guidelines
- **Initial PDFs (Phase 2–3):** 1 RBI circular + 1 HDFC Bank annual report + 1 SEBI circular
- **Full target:** 15–20 PDFs by Phase 6
- **Storage:** `data/raw_pdfs/` (gitignored), vectors in `data/chroma_db/` (gitignored)

**Sample questions:**
- *"What is the minimum capital requirement in the RBI master direction?"*
- *"What is HDFC Bank's net interest income?"*

---
### **Project Structure**
```text
FinancialComplianceRAG/
├── app/app.py                  # Streamlit chat UI
├── data/
│   ├── raw_pdfs/               # PDF corpus (gitignored)
│   └── chroma_db/              # Vector store (gitignored)
├── docs/
│   ├── PROJECT_SPEC.md         # Master technical specification
│   └── PHASE_LOG.md            # Per-phase learning notes
├── notebooks/                  # RAG workflow notebook
├── scripts/                    # Download / utility scripts
├── src/                        # Core Python modules
├── tests/                      # Phase checkpoint tests
├── requirements.txt
├── .env.example
└── README.md
```

---
### **How It Works**
1. **Ingest** — PyMuPDF extracts text from PDFs with page metadata (`src/ingest_docs.py`).
2. **Chunk** — Paragraph-aware splitting preserves semantic meaning (`src/ingest_docs.py`).
3. **Embed** — Sentence-Transformers converts chunks to vectors (`src/embeddings.py`).
4. **Store** — ChromaDB persists embeddings + metadata (`src/vectorstore.py`).
5. **Retrieve** — User query → top-5 similar chunks (`src/retriever.py`).
6. **Generate** — OpenRouter LLM answers strictly from context (`src/generator.py`).
7. **Chat** — Streamlit UI displays answer + citations (`app/app.py`).

---
### **Build Progress**
| Phase | Name | Status |
|-------|------|--------|
| 0 | Scaffold & Spec | ✅ Complete |
| 1 | Project Setup & MLOps | ⬜ Pending |
| 2 | Document Ingestion | ⬜ Pending |
| 3 | Embeddings & Vector Store | ⬜ Pending |
| 4 | Retrieval System | ⬜ Pending |
| 5 | LLM Generator | ⬜ Pending |
| 6 | Streamlit Chat UI | ⬜ Pending |
| 7 | Containerization (Docker) | ⬜ Pending |

Run scaffold test: `pytest tests/test_phase0_scaffold.py -v`  
Full spec: [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)

---
### **Interactive Application Deployment**
```powershell
cd FinancialComplianceRAG
pip install -r requirements.txt
cp .env.example .env   # add OPENROUTER_API_KEY
streamlit run app/app.py
```

---
### **Technology Stack**
| Layer | Technology |
|-------|------------|
| PDF parsing | PyMuPDF |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (CPU) |
| Vector DB | ChromaDB |
| LLM | OpenRouter (`openrouter/free`) |
| Frontend | Streamlit |
| Config | Pydantic Settings |
| Tests | pytest |
| Deploy | Docker (Phase 7) |

---
### **Getting Started**
1. **Clone:** `git clone https://github.com/jegadeesh17/FinancialComplianceRAG.git`
2. **Install:** `pip install -r requirements.txt`
3. **Configure:** `cp .env.example .env` and add your OpenRouter API key
4. **Test scaffold:** `pytest tests/test_phase0_scaffold.py -v`
5. **Notebook:** Open `notebooks/FinancialComplianceRAG.ipynb`

---
### **Example Use Case**
A compliance analyst at a bank receives an updated RBI Master Direction on KYC requirements. Instead of reading 80 pages, they ask: *"What KYC documents are required for individual customers?"* The system retrieves the relevant paragraph, generates a grounded answer, and cites **RBI_Master_Direction_KYC.pdf, Page 12**.

---
### **Future Improvements**
- Hybrid BM25 + semantic search
- RAGAS faithfulness evaluation
- OCR for scanned PDFs
- Multi-collection routing (regulatory vs. filings)

---
### **Contributors**
- [jegadeesh17](https://github.com/jegadeesh17)

---
### **License**
MIT
