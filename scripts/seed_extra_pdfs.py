"""Create supplementary compliance PDFs for local corpus expansion."""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw_pdfs"

DOCUMENTS: dict[str, list[str]] = {
    "rbi_master_direction_aml.pdf": [
        (
            "RBI Master Direction — Anti Money Laundering and Counter Financing of Terrorism (AML/CFT)\n\n"
            "Regulated entities shall implement anti money laundering and counter financing of terrorism controls. "
            "AML and CFT requirements include customer due diligence, ongoing monitoring, and suspicious transaction reporting."
        ),
        (
            "Section 2 — AML/CFT Obligations\n\n"
            "Banks must monitor transactions for suspicious activity under AML rules and file STRs with the FIU-IND. "
            "Customer due diligence includes verification of identity, beneficial ownership, and risk-based enhanced due diligence."
        ),
        (
            "Section 3 — Master Direction Compliance\n\n"
            "The RBI master direction on AML/CFT prescribes policies, board oversight, and training for regulated entities."
        ),
    ],
    "sebi_lodr_governance.pdf": [
        (
            "SEBI Listing Obligations and Disclosure Requirements — Corporate Governance\n\n"
            "Listed entities must disclose corporate governance practices in their annual report. "
            "The board composition and independent director requirements are prescribed under LODR norms."
        ),
        (
            "Section 5 — Governance Disclosures\n\n"
            "Companies shall publish policies on related party transactions, risk management, and "
            "whistle-blower mechanisms as part of listing obligation compliance."
        ),
    ],
}


def write_pdf(filename: str, pages: list[str]) -> Path:
    dest = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(dest)
    doc.close()
    return dest


def main() -> int:
    created = 0
    for filename, pages in DOCUMENTS.items():
        path = write_pdf(filename, pages)
        print(f"Created {path} ({path.stat().st_size:,} bytes)")
        created += 1
    print(f"Seeded {created} supplementary PDF(s) in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
