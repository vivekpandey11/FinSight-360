import pymupdf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

pdf_path = (
    ROOT
    / "data/raw/financials/TCS"
    / "TCS_Annual_Report_2023-24.pdf"
)

output_dir = ROOT / "data/interim/financials/TCS"
output_dir.mkdir(parents=True, exist_ok=True)

statements = {
    "balance_sheet_FY2024_FY2023.txt": [180],
    "profit_loss_FY2024_FY2023.txt": [181],
    "cash_flow_FY2024_FY2023.txt": [184, 185],
}

doc = pymupdf.open(pdf_path)

for filename, pdf_pages in statements.items():

    extracted = []

    for pdf_page in pdf_pages:
        # PDF page number is 1-based; PyMuPDF index is 0-based
        page = doc[pdf_page - 1]

        extracted.append(
            f"\n===== PDF PAGE {pdf_page} =====\n"
        )

        extracted.append(page.get_text("text"))

    output_path = output_dir / filename

    output_path.write_text(
        "\n".join(extracted),
        encoding="utf-8"
    )

    print(
        f"Saved: {filename} "
        f"({output_path.stat().st_size:,} bytes)"
    )

doc.close()

print("\nFY2024/FY2023 statement extraction complete.")
