from pathlib import Path
import pymupdf

ROOT = Path.cwd()

REPORTS = {
    "FY2026_FY2025": {
        "pdf": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2025-26.pdf",
        "bs": [285, 286],
        "pl": [287, 288],
        "cf": [294, 295],
    },
    "FY2024_FY2023": {
        "pdf": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2023-24.pdf",
        "bs": [270, 271],
        "pl": [272, 273],
        "cf": [279, 280],
    },
    "FY2023_FY2022": {
        "pdf": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2022-23.pdf",
        "bs": [271, 272],
        "pl": [273, 274],
        "cf": [280, 281],
    },
}

OUT = ROOT / "data/interim/financials/INFY"
OUT.mkdir(parents=True, exist_ok=True)

def extract_pages(doc, pages):
    chunks = []

    for page_no in pages:
        text = doc[page_no - 1].get_text("text")
        chunks.append(
            f"\n===== PDF PAGE {page_no} =====\n{text}"
        )

    return "\n".join(chunks)

for label, cfg in REPORTS.items():

    print(f"\nProcessing {label}...")

    doc = pymupdf.open(cfg["pdf"])

    outputs = {
        "balance_sheet": extract_pages(doc, cfg["bs"]),
        "profit_loss": extract_pages(doc, cfg["pl"]),
        "cash_flow": extract_pages(doc, cfg["cf"]),
    }

    for statement, content in outputs.items():

        path = OUT / f"{statement}_{label}.txt"
        path.write_text(content, encoding="utf-8")

        print(
            f"{statement:15s} -> "
            f"{path.name} ({len(content):,} chars)"
        )

    doc.close()

print("\nINFOSYS EXACT STATEMENT EXTRACTION COMPLETE")
