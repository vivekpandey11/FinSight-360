import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "data/interim/financials/TCS"
    / "balance_sheet_FY2026_FY2025.txt"
)

OUTPUT = (
    ROOT / "data/interim/financials/TCS"
    / "parsed_balance_sheet_FY2026_FY2025.csv"
)

text = INPUT.read_text(encoding="utf-8")


def num(value):
    value = value.strip()

    if value == "-":
        return 0.0

    negative = value.startswith("(") and value.endswith(")")

    value = (
        value.replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    result = float(value)
    return -result if negative else result


def pair_after(label, occurrence=1):
    matches = list(
        re.finditer(
            re.escape(label),
            text,
            flags=re.IGNORECASE
        )
    )

    if len(matches) < occurrence:
        raise ValueError(
            f"{label}: occurrence {occurrence} not found"
        )

    chunk = text[matches[occurrence - 1].end():]

    lines = [
        x.strip()
        for x in chunk.splitlines()
        if x.strip()
    ]

    values = []

    for line in lines[:10]:

        # Skip accounting note references
        if re.fullmatch(
            r"\d+[A-Za-z]?(?:\([a-z]\))?",
            line
        ):
            continue

        if re.fullmatch(
            r"-|\(?[\d,]+(?:\.\d+)?\)?",
            line
        ):
            values.append(num(line))

        if len(values) == 2:
            return values

    raise ValueError(f"Values not found: {label}")


fields = {
    "property_plant_equipment":
        ("Property, plant and equipment", 1),

    "cash_and_equivalents":
        ("Cash and cash equivalents", 1),

    "current_assets":
        ("Total current assets", 1),

    "total_assets":
        ("TOTAL ASSETS", 1),

    "share_capital":
        ("Share capital", 1),

    "shareholders_equity":
        ("Equity attributable to shareholders of the Company", 1),

    "total_equity":
        ("Total equity", 1),

    "trade_payables":
        ("Trade payables", 1),

    "current_liabilities":
        ("Total current liabilities", 1),

    "total_equity_and_liabilities":
        ("TOTAL EQUITY AND LIABILITIES", 1),
}

rows = {
    2026: {"company_code": "TCS", "fiscal_year": 2026},
    2025: {"company_code": "TCS", "fiscal_year": 2025},
}

for field, (label, occurrence) in fields.items():

    fy26, fy25 = pair_after(label, occurrence)

    rows[2026][field] = fy26
    rows[2025][field] = fy25


# Trade receivables need billed + unbilled,
# separately for non-current and current sections.

# Values verified from the consolidated balance sheet.
rows[2026]["receivables"] = 99 + 114 + 57630 + 10084
rows[2025]["receivables"] = 91 + 38 + 50142 + 8904


for year in [2026, 2025]:

    row = rows[year]

    row["total_liabilities"] = (
        row["total_equity_and_liabilities"]
        - row["total_equity"]
    )


df = pd.DataFrame([
    rows[2026],
    rows[2025]
])

df.to_csv(OUTPUT, index=False)


print("TCS Balance Sheet parsing complete")
print("=" * 75)

print(
    df[
        [
            "fiscal_year",
            "cash_and_equivalents",
            "receivables",
            "current_assets",
            "total_assets",
            "shareholders_equity",
            "total_equity",
            "current_liabilities",
            "total_liabilities"
        ]
    ].to_string(index=False)
)


print("\nAccounting validation")
print("-" * 75)

for _, row in df.iterrows():

    equation_difference = (
        row["total_assets"]
        - row["total_equity"]
        - row["total_liabilities"]
    )

    statement_difference = (
        row["total_assets"]
        - row["total_equity_and_liabilities"]
    )

    print(
        f"FY{int(row['fiscal_year'])}: "
        f"Assets-(Equity+Liabilities)="
        f"{equation_difference:.2f}, "
        f"Statement difference="
        f"{statement_difference:.2f}"
    )


print(f"\nSaved: {OUTPUT}")
