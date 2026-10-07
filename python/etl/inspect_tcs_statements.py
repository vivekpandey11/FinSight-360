import pymupdf
from pathlib import Path

pdf_path = Path("data/raw/financials/TCS/TCS_Annual_Report_2025-26.pdf")
doc = pymupdf.open(pdf_path)

# Human PDF pages 166-173
for pdf_page in range(166, 174):
    page = doc[pdf_page - 1]

    print("\n" + "=" * 90)
    print(f"PDF PAGE {pdf_page}")
    print("=" * 90)

    text = page.get_text("text")

    # Keep terminal output manageable
    print(text[:5000])

doc.close()
