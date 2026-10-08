import pymupdf
from pathlib import Path

pdf_path = Path(
    "data/raw/financials/TCS/"
    "TCS_Annual_Report_2025-26.pdf"
)

if not pdf_path.exists():
    raise FileNotFoundError(
        f"Annual report not found: {pdf_path}"
    )

doc = pymupdf.open(pdf_path)

search_terms = [
    "cash and cash equivalents",
    "current investments",
    "non-current investments",
    "borrowings",
    "lease liabilities",
    "equity shares",
    "share capital"
]

print("\n" + "=" * 100)
print("FINSIGHT 360 — TCS FY2026 VALUATION BRIDGE SOURCE SEARCH")
print("=" * 100)

matches = []

for page_no in range(len(doc)):

    text = doc[page_no].get_text()

    text_lower = text.lower()

    found_terms = [
        term
        for term in search_terms
        if term in text_lower
    ]

    if found_terms:

        matches.append(
            (
                page_no + 1,
                found_terms
            )
        )

        print(
            f"\nPDF PAGE {page_no + 1}"
        )

        print(
            "Matched: "
            + ", ".join(found_terms)
        )

        print("-" * 100)

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for i, line in enumerate(lines):

            line_lower = line.lower()

            if any(
                term in line_lower
                for term in search_terms
            ):

                start = max(
                    0,
                    i - 3
                )

                end = min(
                    len(lines),
                    i + 8
                )

                print(
                    "\n".join(
                        lines[start:end]
                    )
                )

                print(
                    "-" * 50
                )

print("\n" + "=" * 100)

print(
    f"Pages with relevant terms: "
    f"{len(matches)}"
)

print(
    "Search completed successfully."
)

doc.close()
