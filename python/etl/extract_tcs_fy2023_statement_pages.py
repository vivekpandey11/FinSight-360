from pathlib import Path
import pymupdf

ROOT = Path.cwd()

pdf_path = (
    ROOT / "data" / "raw" / "financials" /
    "TCS" / "TCS_Annual_Report_2022-23.pdf"
)

output_dir = (
    ROOT / "data" / "interim" / "financials" / "TCS"
)

output_dir.mkdir(parents=True, exist_ok=True)

statements = {
    "balance_sheet_FY2023_FY2022.txt": [190],
    "profit_loss_FY2023_FY2022.txt": [191],
    "cash_flow_FY2023_FY2022.txt": [194, 195],
}

doc = pymupdf.open(pdf_path)

for filename, pdf_pages in statements.items():

    parts = []

    for pdf_page in pdf_pages:
        page = doc[pdf_page - 1]

        parts.append(
            f"\n{'=' * 70}\n"
            f"PDF PAGE {pdf_page}\n"
            f"{'=' * 70}\n"
        )

        parts.append(page.get_text("text"))

    output_path = output_dir / filename

    output_path.write_text(
        "\n".join(parts),
        encoding="utf-8"
    )

    print(
        f"SAVED -> {filename} "
        f"({output_path.stat().st_size:,} bytes)"
    )

doc.close()

print("\nTCS FY2023/FY2022 statement extraction complete.")
