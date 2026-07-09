"""Product UI styles for Financial Intelligence Copilot Streamlit app."""

PRODUCT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
    max-width: 1180px;
}

.fic-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0f766e 100%);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    color: #f8fafc;
    margin-bottom: 1.25rem;
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18);
}

.fic-hero h1 {
    font-size: 1.85rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.02em;
}

.fic-hero p {
    margin: 0;
    opacity: 0.9;
    font-size: 1rem;
    line-height: 1.5;
}

.fic-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
}

.fic-pill {
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 999px;
    padding: 0.3rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 500;
}

.fic-section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin: 0 0 0.5rem 0;
}

.fic-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.65rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.fic-card-muted {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.55rem;
}

.fic-sentiment-positive { color: #059669; font-weight: 600; }
.fic-sentiment-negative { color: #dc2626; font-weight: 600; }
.fic-sentiment-neutral { color: #64748b; font-weight: 600; }

.fic-badge-ok {
    display: inline-block;
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.fic-badge-low {
    display: inline-block;
    background: #fff7ed;
    color: #c2410c;
    border: 1px solid #fed7aa;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.fic-citation {
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 0.2rem 0.55rem;
    font-size: 0.78rem;
    margin: 0.15rem 0.35rem 0.15rem 0;
}

.fic-doc-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #f1f5f9;
}

.fic-doc-row:last-child { border-bottom: none; }

.fic-doc-name {
    font-size: 0.84rem;
    color: #0f172a;
    font-weight: 500;
    line-height: 1.35;
    word-break: break-word;
}

.fic-doc-meta {
    font-size: 0.72rem;
    color: #64748b;
    white-space: nowrap;
}

.fic-category-regulatory { border-left: 3px solid #2563eb; }
.fic-category-annual_report { border-left: 3px solid #059669; }
.fic-category-insurance { border-left: 3px solid #7c3aed; }
.fic-category-exam_reference { border-left: 3px solid #d97706; }

[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

div[data-testid="stChatMessage"] {
    background: transparent;
}

div[data-testid="stChatMessageContent"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 0.85rem 1rem;
}
</style>
"""

CATEGORY_LABELS = {
    "regulatory": "Regulatory",
    "annual_report": "Annual reports",
    "insurance": "Insurance",
    "exam_reference": "Exam reference",
}

SAMPLE_QUERIES = {
    "regulatory": {
        "label": "RBI KYC rules",
        "query": "What are RBI KYC requirements for individual customers?",
    },
    "annual_report": {
        "label": "HDFC NII",
        "query": "What was HDFC Bank net interest income in the annual report?",
    },
    "insurance": {
        "label": "IRDAI products",
        "query": "What does IRDAI say about life insurance product approval?",
    },
    "exam_reference": {
        "label": "Research analyst ethics",
        "query": "What are SEBI research analyst conflict-of-interest rules?",
    },
}


def citation_chips_html(citations: list) -> str:
    """Render citations as HTML chips for the product UI."""
    if not citations:
        return '<span class="fic-doc-meta">No sources cited</span>'

    grouped: dict[str, set[int]] = {}
    for c in citations:
        source = c.source if hasattr(c, "source") else c.get("source", "")
        page = int(c.page if hasattr(c, "page") else c.get("page", 0))
        grouped.setdefault(source, set()).add(page)

    chips: list[str] = []
    for source, pages in grouped.items():
        ordered = sorted(p for p in pages if p > 0)
        page_text = ", ".join(str(p) for p in ordered[:4])
        if len(ordered) > 4:
            page_text += "+"
        short = source if len(source) <= 36 else source[:33] + "..."
        chips.append(
            f'<span class="fic-citation" title="{source}">{short} · p.{page_text}</span>'
        )
    return "".join(chips)
