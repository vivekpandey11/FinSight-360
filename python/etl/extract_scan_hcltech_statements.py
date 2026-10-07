from pathlib import Path
import pymupdf
import re

ROOT = Path.cwd()
OUT = ROOT / "data/interim/financials/HCLTECH"
OUT.mkdir(parents=True, exist_ok=True)

REPORTS = {
    "FY2026_FY2025": {
        "pdf": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2025-26.pdf",
        "bs": [373, 374],
        "pl": [375, 376],
        "cf": [379, 380],
    },
    "FY2024_FY2023": {
        "pdf": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2023-24.pdf",
        "bs": [286, 287],
        "pl": [288, 289],
        "cf": [291, 292],
    },
    "FY2023_FY2022": {
        "pdf": ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2022-23.pdf",
        "bs": [282, 283],
        "pl": [284, 285],
        "cf": [287, 288],
    },
}

PATTERNS = [
    r"revenue",
    r"other income",
    r"employee benefit",
    r"employee cost",
    r"finance cost",
    r"depreciation",
    r"profit before tax",
    r"tax expense",
    r"current tax",
    r"deferred tax",
    r"profit for the year",
    r"profit for the period",
    r"owners of",
    r"equity holders",
    r"earnings per",
    r"basic",
    r"property.*plant",
    r"trade receivables",
    r"cash and cash equivalents",
    r"current assets",
    r"total assets",
    r"trade payables",
    r"current liabilities",
    r"non-current liabilities",
    r"total liabilities",
    r"total equity",
    r"net cash.*operating",
    r"purchase.*property",
    r"purchase.*intangible",
    r"capital expenditure",
    r"net cash.*investing",
    r"net cash.*financing",
    r"dividend",
]

regex = re.compile("|".join(PATTERNS), re.I)


def extract(doc, pages):
    chunks = []

    for page_no in pages:
        text = doc[page_no - 1].get_text("text")
        chunks.append(
            f"\n===== PDF PAGE {page_no} =====\n{text}"
        )

    return "\n".join(chunks)


for label, cfg in REPORTS.items():

    print("\n" + "=" * 100)
    print(label)
    print("=" * 100)

    doc = pymupdf.open(cfg["pdf"])

    statements = {
        "balance_sheet": extract(doc, cfg["bs"]),
        "profit_loss": extract(doc, cfg["pl"]),
        "cash_flow": extract(doc, cfg["cf"]),
    }

    for statement, content in statements.items():

        path = OUT / f"{statement}_{label}.txt"
        path.write_text(content, encoding="utf-8")

        print(
            f"\n{statement.upper()} "
            f"-> {path.name}"
        )

        lines = content.splitlines()

        for i, line in enumerate(lines):

            if regex.search(line):

                start = i
                end = min(len(lines), i + 7)

                print(f"\n--- lines {start+1}-{end} ---")

                for j in range(start, end):
                    print(
                        f"{j+1:04d}: {lines[j]}"
                    )

    doc.close()

print("\nHCLTECH EXACT EXTRACTION + FINANCIAL SCAN COMPLETE")
