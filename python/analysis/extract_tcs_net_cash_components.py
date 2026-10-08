import pymupdf
from pathlib import Path
import re

pdf_path = Path(
    "data/raw/financials/TCS/"
    "TCS_Annual_Report_2025-26.pdf"
)

doc = pymupdf.open(pdf_path)

terms = [
    "current investments",
    "non-current investments",
    "other bank balances",
    "bank deposits",
    "investments carried at fair value",
    "investments carried at amortised cost",
    "lease liabilities",
    "borrowings"
]

output_path = Path(
    "data/interim/financials/TCS/"
    "TCS_FY2026_net_cash_source_extract.txt"
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

blocks = []

for page_index in range(len(doc)):

    text = doc[page_index].get_text("text")

    lower = text.lower()

    matched = [
        term
        for term in terms
        if term in lower
    ]

    if not matched:
        continue

    lines = [
        re.sub(r"\s+", " ", x).strip()
        for x in text.splitlines()
        if x.strip()
    ]

    selected = []

    for i, line in enumerate(lines):

        if any(
            term in line.lower()
            for term in terms
        ):

            start = max(0, i - 8)
            end = min(
                len(lines),
                i + 18
            )

            selected.extend(
                lines[start:end]
            )

    # remove duplicate lines while preserving order
    selected = list(
        dict.fromkeys(selected)
    )

    block = (
        "\n"
        + "=" * 100
        + f"\nPDF PAGE {page_index + 1}"
        + "\nMATCHED: "
        + ", ".join(matched)
        + "\n"
        + "-" * 100
        + "\n"
        + "\n".join(selected)
        + "\n"
    )

    blocks.append(block)

doc.close()

output_path.write_text(
    "\n".join(blocks),
    encoding="utf-8"
)

print("\n" + "=" * 100)
print("TCS FY2026 — NET CASH SOURCE EXTRACTION")
print("=" * 100)

print(
    f"\nRelevant pages found: {len(blocks)}"
)

print(
    f"Saved full extraction -> {output_path}"
)

print("\n" + "=" * 100)
print("TARGETED FY2026 LINES")
print("=" * 100)

full_text = "\n".join(blocks)

for line in full_text.splitlines():

    lower = line.lower()

    if any(
        term in lower
        for term in terms
    ):
        print(line)

print(
    "\nExtraction completed successfully."
)
