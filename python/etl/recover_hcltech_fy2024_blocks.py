from pathlib import Path
import pymupdf

PDF = Path(
    "data/raw/financials/HCLTECH/"
    "HCLTECH_Annual_Report_2023-24.pdf"
)

doc = pymupdf.open(PDF)

pages = {
    "BALANCE_SHEET": [286, 287],
    "PROFIT_LOSS": [288, 289],
    "CASH_FLOW": [291, 292],
}

for section, page_numbers in pages.items():

    print("\n" + "=" * 110)
    print(section)
    print("=" * 110)

    for page_no in page_numbers:

        page = doc[page_no - 1]

        print(f"\n{'-'*40} PDF PAGE {page_no} {'-'*40}")

        blocks = page.get_text("blocks")

        blocks = sorted(
            blocks,
            key=lambda b: (round(b[1], 1), round(b[0], 1))
        )

        for i, block in enumerate(blocks, start=1):

            x0, y0, x1, y1, text, *_ = block

            cleaned = " | ".join(
                line.strip()
                for line in text.splitlines()
                if line.strip()
            )

            if cleaned:
                print(
                    f"{i:03d} "
                    f"[x={x0:.0f}-{x1:.0f}, "
                    f"y={y0:.0f}-{y1:.0f}] "
                    f"{cleaned}"
                )

doc.close()

print("\nHCLTECH FY2024 BLOCK RECOVERY COMPLETE")
