import pymupdf
from pathlib import Path

pdf_path = Path("data/raw/financials/TCS/TCS_Annual_Report_2025-26.pdf")

doc = pymupdf.open(pdf_path)

keywords = [
    "consolidated balance sheet",
    "consolidated statement of profit and loss",
    "consolidated statement of cash flows",
    "consolidated cash flow statement",
]

print(f"Total PDF pages: {len(doc)}")
print("\nPotential financial statement pages")
print("=" * 60)

for page_no, page in enumerate(doc):
    text = page.get_text().lower()

    for keyword in keywords:
        if keyword in text:
            print(
                f"PDF page {page_no + 1}: "
                f"{keyword.upper()}"
            )

doc.close()
