import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data/interim/financials/TCS"
    / "profit_loss_FY2026_FY2025.txt"
)

OUTPUT = (
    ROOT
    / "data/interim/financials/TCS"
    / "parsed_profit_loss_FY2026_FY2025.csv"
)

text = INPUT.read_text(encoding="utf-8")


def to_number(value):
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

    number = float(value)

    return -number if negative else number


def extract_pair(label, allow_note=False):
    pattern = rf"{re.escape(label)}\s*\n"

    match = re.search(pattern, text, flags=re.IGNORECASE)

    if not match:
        raise ValueError(f"Label not found: {label}")

    after = text[match.end():]

    lines = [
        line.strip()
        for line in after.splitlines()
        if line.strip()
    ]

    values = []

    for line in lines[:8]:

        # Ignore accounting note references such as 12, 13, 16, 17, 15(a)
        if re.fullmatch(r"\d+[A-Za-z]?(?:\([a-z]\))?", line):
            if not allow_note:
                continue

        if re.fullmatch(
            r"-|\(?[\d,]+(?:\.\d+)?\)?",
            line
        ):
            values.append(to_number(line))

        if len(values) == 2:
            return values[0], values[1]

    raise ValueError(
        f"Could not extract two values for: {label}"
    )


fields = {
    "revenue": "Revenue from operations",
    "other_income": "Other income",
    "total_income": "TOTAL INCOME",
    "employee_benefit_expense": "Employee benefit expenses",
    "equipment_software_cost": "Cost of equipment and software licences",
    "finance_cost": "Finance costs",
    "depreciation_amortization": "Depreciation and amortisation expense",
    "other_expenses": "Other expenses",
    "total_expenses": "TOTAL EXPENSES",
    "profit_before_exceptional_items_tax":
        "PROFIT BEFORE EXCEPTIONAL ITEMS AND TAX",
    "profit_before_tax": "PROFIT BEFORE TAX",
    "total_tax_expense": "TOTAL TAX EXPENSE",
    "net_income": "PROFIT FOR THE YEAR",
    "eps": "Earnings per equity share:- Basic and diluted (J)",
}

rows = {
    2026: {
        "company_code": "TCS",
        "fiscal_year": 2026
    },
    2025: {
        "company_code": "TCS",
        "fiscal_year": 2025
    }
}

for field, label in fields.items():
    fy26, fy25 = extract_pair(label)

    rows[2026][field] = fy26
    rows[2025][field] = fy25


df = pd.DataFrame([
    rows[2026],
    rows[2025]
])

# Derived analytical metrics
df["ebit"] = (
    df["profit_before_exceptional_items_tax"]
    + df["finance_cost"]
)

df["ebitda"] = (
    df["ebit"]
    + df["depreciation_amortization"]
)

df["ebitda_margin"] = df["ebitda"] / df["revenue"]
df["net_margin"] = df["net_income"] / df["revenue"]

df.to_csv(OUTPUT, index=False)

print("TCS P&L parsing complete")
print("=" * 70)

print(
    df[
        [
            "fiscal_year",
            "revenue",
            "ebitda",
            "ebit",
            "profit_before_tax",
            "net_income",
            "eps"
        ]
    ].to_string(index=False)
)

print("\nValidation")
print("-" * 70)

for _, row in df.iterrows():

    income_check = (
        row["revenue"]
        + row["other_income"]
        - row["total_income"]
    )

    pat_check = (
        row["profit_before_tax"]
        - row["total_tax_expense"]
        - row["net_income"]
    )

    print(
        f"FY{int(row['fiscal_year'])}: "
        f"Total income difference={income_check:.2f}, "
        f"PAT difference={pat_check:.2f}"
    )

print(f"\nSaved: {OUTPUT}")
