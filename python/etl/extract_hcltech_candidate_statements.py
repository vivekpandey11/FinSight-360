from pathlib import Path
import pymupdf
import re

ROOT = Path.cwd()

REPORTS = {
    "FY2026_FY2025": {
        "file": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2025-26.pdf",
        "pages": range(373, 381),
    },
    "FY2024_FY2023": {
        "file": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2023-24.pdf",
        "pages": range(286, 293),
    },
    "FY2023_FY2022": {
        "file": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2022-23.pdf",
        "pages": range(282, 289),
    },
}

OUT = ROOT / "data/interim/financials/HCLTECH"
OUT.mkdir(parents=True, exist_ok=True)

keywords = [
    "consolidated balance sheet",
    "consolidated statement of financial position",
    "consolidated statement of profit",
    "consolidated statement of income",
    "consolidated income statement",
    "consolidated statement of cash flows",
    "revenue",
    "profit before tax",
    "profit for the year",
    "profit for the period",
    "total assets",
    "total equity",
    "cash and cash equivalents",
    "net cash generated",
    "net cash flow",
    "earnings per equity share",
]

for label, cfg in REPORTS.items():

    print("\n" + "=" * 95)
    print(label, "-", cfg["file"].name)
    print("=" * 95)

    doc = pymupdf.open(cfg["file"])
    combined = []

    for page_no in cfg["pages"]:

        if not (1 <= page_no <= len(doc)):
            continue

        text = doc[page_no - 1].get_text("text")
        normalized = re.sub(r"\s+", " ", text).lower()

        hits = [
            keyword
            for keyword in keywords
            if keyword in normalized
        ]

        first_lines = [
            x.strip()
            for x in text.splitlines()
            if x.strip()
        ][:6]

        print(f"\nPDF PAGE {page_no}")
        print("Hits:", ", ".join(hits) if hits else "NONE")

        for line in first_lines:
            print("   ", line[:160])

        combined.append(
            f"\n\n{'='*30} PDF PAGE {page_no} {'='*30}\n\n{text}"
        )

    output = OUT / f"{label}_candidate_statements.txt"
    output.write_text(
        "".join(combined),
        encoding="utf-8"
    )

    print(f"\nSAVED -> {output}")

    doc.close()

print("\nHCLTECH CANDIDATE STATEMENT EXTRACTION COMPLETE")
