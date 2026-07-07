"""
Download initial PDF corpus into data/raw_pdfs/.

Run: python scripts/download_docs.py

If a URL fails (sites change links), download manually — see docs/DATA_SOURCES.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw_pdfs"

# Public PDF URLs — update if a host changes their link structure.
DOCUMENTS: list[dict[str, str]] = [
    {
        "filename": "rbi_master_direction_kyc.pdf",
        "url": (
            "https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/"
            "MD18KYCF6E92C82E1E1419D87323E3869BC9F13.pdf"
        ),
        "note": "RBI Master Direction — KYC (AML/CFT)",
    },
    {
        "filename": "hdfc_bank_annual_report.pdf",
        "url": (
            "https://www.hdfcbank.com/content/bbp/repositories/"
            "723fb80a-2dde-42a3-9793-7ae1be57c87f/?path=%2FFooter%2FAbout+Us%2F"
            "Investor+Relation%2Fannual+reports%2Fpdf%2F2024%2Fjuly%2F"
            "HDFC-Bank-IAR-FY24.pdf"
        ),
        "note": "HDFC Bank Integrated Annual Report FY2023-24",
    },
    {
        "filename": "sebi_circular_disclosure.pdf",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/1486375066836.pdf",
        "note": "SEBI LODR circular — Business Responsibility Report (disclosure)",
    },
    {
        "filename": "rbi_master_direction_aml.pdf",
        "url": (
            "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566"
        ),
        "note": "RBI Master Direction — AML/CFT (fallback: scripts/seed_extra_pdfs.py)",
        "optional": True,
    },
    {
        "filename": "sebi_lodr_governance.pdf",
        "url": "https://www.sebi.gov.in/legal/circulars/2023/aug/corporate-governance-disclosures.pdf",
        "note": "SEBI LODR governance circular (fallback: scripts/seed_extra_pdfs.py)",
        "optional": True,
    },
]

TIMEOUT = httpx.Timeout(120.0, connect=15.0)
MIN_PDF_BYTES = 10_000
PDF_MAGIC = b"%PDF"


def _is_pdf_content(content: bytes, content_type: str | None) -> bool:
    if content[:4] == PDF_MAGIC:
        return True
    if content_type and "pdf" in content_type.lower():
        return True
    return False


def download_document(client: httpx.Client, doc: dict[str, str], out_dir: Path) -> bool:
    filename = doc["filename"]
    url = doc["url"]
    dest = out_dir / filename

    print(f"Downloading {filename} ...")
    try:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"  FAILED: HTTP error — {exc}")
        return False

    content = response.content
    content_type = response.headers.get("content-type")

    if not _is_pdf_content(content, content_type):
        print(
            f"  FAILED: Response is not a PDF (got {content_type!r}, "
            f"{len(content)} bytes). Download manually — see docs/DATA_SOURCES.md"
        )
        return False

    if len(content) < MIN_PDF_BYTES:
        print(f"  FAILED: File too small ({len(content)} bytes) — likely not a real PDF.")
        return False

    dest.write_bytes(content)
    print(f"  OK: saved {dest} ({len(content):,} bytes)")
    return True


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    failed: list[str] = []

    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": "FinancialComplianceRAG/1.0"}) as client:
        for doc in DOCUMENTS:
            if download_document(client, doc, OUTPUT_DIR):
                ok += 1
            elif doc.get("optional"):
                print(f"  Optional doc skipped: {doc['filename']}")
            else:
                failed.append(doc["filename"])

    print()
    print(f"Downloaded {ok}/{len(DOCUMENTS)} PDFs to {OUTPUT_DIR}")
    if failed:
        print("Manual download needed for:")
        for name in failed:
            print(f"  - {name}")
        print("See docs/DATA_SOURCES.md for source links.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
