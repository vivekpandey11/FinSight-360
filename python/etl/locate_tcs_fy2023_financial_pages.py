from pathlib import Path
import pymupdf

ROOT = Path.cwd()
pdf_path = ROOT / "data" / "raw" / "financials" / "TCS" / "TCS_Annual_Report_2022-23.pdf"

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

doc = pymupdf.open(pdf_path)

print(f"File: {pdf_path.name}")
print(f"Total pages: {len(doc)}")
print("\n=== POSSIBLE FINANCIAL STATEMENT PAGES ===")

keywords = [
    "consolidated balance sheet",
    "consolidated statement of profit and loss",
    "consolidated statement of cash flows",
]

for i, page in enumerate(doc):
    text = page.get_text().lower()

    matches = [k for k in keywords if k in text]

    if matches:
        print(f"\nPDF page {i + 1}")
        for m in matches:
            print(f"  -> {m}")

doc.close()
