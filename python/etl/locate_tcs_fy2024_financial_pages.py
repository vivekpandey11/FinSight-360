import pymupdf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PDF = (
    ROOT
    / "data/raw/financials/TCS"
    / "TCS_Annual_Report_2023-24.pdf"
)

terms = [
    "consolidated balance sheet",
    "consolidated statement of profit and loss",
    "consolidated statement of cash flows",
    "consolidated cash flow statement",
]

doc = pymupdf.open(PDF)

print(f"File: {PDF.name}")
print(f"Total PDF pages: {len(doc)}")
print("\nPotential financial statement pages:")

for index, page in enumerate(doc):
    text = page.get_text("text")
    lower = text.lower()

    for term in terms:
        if term in lower:
            print(
                f"PDF page {index + 1}: "
                f"{term.upper()}"
            )

doc.close()
