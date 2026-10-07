from pathlib import Path
import pymupdf

ROOT = Path.cwd()

REPORTS = {
    "FY2026_FY2025": {
        "file": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2025-26.pdf",
        "pages": range(284, 296),
    },
    "FY2024_FY2023": {
        "file": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2023-24.pdf",
        "pages": range(269, 281),
    },
    "FY2023_FY2022": {
        "file": ROOT / "data/raw/financials/INFY/INFY_Annual_Report_2022-23.pdf",
        "pages": range(270, 282),
    },
}

OUT = ROOT / "data/interim/financials/INFY"
OUT.mkdir(parents=True, exist_ok=True)

keywords = [
    "consolidated balance sheet",
    "consolidated statement of profit and loss",
    "consolidated statement of comprehensive income",
    "consolidated statement of cash flows",
    "revenues",
    "revenue from operations",
    "profit before tax",
    "profit for the year",
    "total assets",
    "total equity",
    "cash and cash equivalents",
    "net cash generated",
]

for label, cfg in REPORTS.items():

    doc = pymupdf.open(cfg["file"])

    print("\n" + "=" * 90)
    print(label, "-", cfg["file"].name)
    print("=" * 90)

    combined = []

    for pdf_page in cfg["pages"]:

        if pdf_page < 1 or pdf_page > len(doc):
            continue

        # Human PDF page number -> zero-based PyMuPDF index
        text = doc[pdf_page - 1].get_text("text")

        low = " ".join(text.lower().split())

        hits = [k for k in keywords if k in low]

        if hits:
            print(
                f"PDF page {pdf_page:3d} | "
                f"hits: {', '.join(hits)}"
            )

        combined.append(
            f"\n\n{'='*30} PDF PAGE {pdf_page} {'='*30}\n\n{text}"
        )

    output = OUT / f"{label}_candidate_statements.txt"
    output.write_text("".join(combined), encoding="utf-8")

    print(f"SAVED -> {output}")

    doc.close()

print("\nINFOSYS CANDIDATE STATEMENT EXTRACTION COMPLETE")
