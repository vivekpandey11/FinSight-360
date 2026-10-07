from pathlib import Path
import pymupdf
import re

ROOT = Path.cwd()

FILES = [
    ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2025-26.pdf",
    ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2023-24.pdf",
    ROOT / "data/raw/financials/HCLTECH/HCLTECH_Annual_Report_2022-23.pdf",
]

patterns = {
    "BALANCE SHEET": [
        r"consolidated balance sheet",
        r"consolidated statement of financial position",
    ],
    "PROFIT & LOSS": [
        r"consolidated statement of profit and loss",
        r"consolidated statement of income",
    ],
    "CASH FLOW": [
        r"consolidated statement of cash flows",
        r"consolidated cash flow statement",
    ],
}

for pdf_path in FILES:

    print("\n" + "=" * 95)
    print(pdf_path.name)
    print("=" * 95)

    if not pdf_path.exists():
        print("FILE NOT FOUND")
        continue

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"PDF OPEN ERROR: {e}")
        continue

    print(f"Total pages: {len(doc)}")

    found = {key: [] for key in patterns}

    for page_number, page in enumerate(doc, start=1):

        try:
            text = page.get_text("text")
        except Exception:
            continue

        normalized = re.sub(r"\s+", " ", text).lower()

        for statement, regex_list in patterns.items():

            if any(
                re.search(pattern, normalized, flags=re.I)
                for pattern in regex_list
            ):
                found[statement].append(page_number)

    for statement, pages in found.items():
        print(f"{statement:20s}: {pages}")

    doc.close()

print("\nHCLTECH BATCH PAGE SCAN COMPLETE")
