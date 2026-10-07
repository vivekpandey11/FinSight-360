from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data/raw/financials/TCS/TCS_Annual_Report_2025-26.pdf"
OUT = ROOT / "data/interim/financials/TCS"

OUT.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(PDF)

pages = {
    "balance_sheet": [166],
    "profit_loss": [167],
    "cash_flow": [172, 173],
}

for name, page_numbers in pages.items():
    chunks = []

    for number in page_numbers:
        text = doc[number - 1].get_text("text")
        chunks.append(f"--- PDF PAGE {number} ---\n{text}")

    output = OUT / f"{name}_FY2026_FY2025.txt"
    output.write_text("\n\n".join(chunks), encoding="utf-8")

    print(f"{name:<15} -> {output.name}")

doc.close()

print("\nTCS statement extraction complete.")
