import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "data/interim/financials/TCS"
    / "cash_flow_FY2026_FY2025.txt"
)

OUTPUT = (
    ROOT / "data/interim/financials/TCS"
    / "parsed_cash_flow_FY2026_FY2025.csv"
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


def pair_after(label):
    match = re.search(
        re.escape(label),
        text,
        flags=re.IGNORECASE
    )

    if not match:
        raise ValueError(f"Label not found: {label}")

    lines = [
        line.strip()
        for line in text[match.end():].splitlines()
        if line.strip()
    ]

    values = []

    for line in lines[:8]:

        if re.fullmatch(
            r"-|\(?[\d,]+(?:\.\d+)?\)?",
            line
        ):
            values.append(num(line))

        if len(values) == 2:
            return values[0], values[1]

    raise ValueError(f"Could not extract values: {label}")


fields = {
    "cash_from_operations":
        "Net cash flows generated from operating activities",

    "ppe_purchase":
        "Payment for purchase of property, plant and equipment",

    "intangible_purchase":
        "Payment for purchase of intangible assets",

    "cash_from_investing":
        "Net cash flows used in investing activities",

    "cash_from_financing":
        "Net cash flows used in financing activities",

    "dividends_paid":
        "Dividend paid",

    "net_change_in_cash":
        "Net change in cash and cash equivalents",

    "opening_cash":
        "Cash and cash equivalents at the beginning of the year",

    "fx_effect_on_cash":
        "Exchange difference on translation of foreign currency cash and cash equivalents",

    "closing_cash":
        "Cash and cash equivalents at the end of the year",
}


rows = {
    2026: {"company_code": "TCS", "fiscal_year": 2026},
    2025: {"company_code": "TCS", "fiscal_year": 2025},
}


for field, label in fields.items():

    fy26, fy25 = pair_after(label)

    rows[2026][field] = fy26
    rows[2025][field] = fy25


for year in [2026, 2025]:

    row = rows[year]

    # Statement reports purchases as negative cash flows.
    # Standardized CapEx is stored as a positive magnitude.
    row["capital_expenditure"] = -(
        row["ppe_purchase"]
        + row["intangible_purchase"]
    )

    row["free_cash_flow"] = (
        row["cash_from_operations"]
        - row["capital_expenditure"]
    )


df = pd.DataFrame([
    rows[2026],
    rows[2025]
])

df.to_csv(OUTPUT, index=False)


print("TCS Cash Flow parsing complete")
print("=" * 78)

print(
    df[
        [
            "fiscal_year",
            "cash_from_operations",
            "capital_expenditure",
            "free_cash_flow",
            "cash_from_investing",
            "cash_from_financing",
            "dividends_paid",
            "closing_cash"
        ]
    ].to_string(index=False)
)


print("\nCash reconciliation")
print("-" * 78)

for _, row in df.iterrows():

    cash_difference = (
        row["opening_cash"]
        + row["net_change_in_cash"]
        + row["fx_effect_on_cash"]
        - row["closing_cash"]
    )

    fcf_difference = (
        row["cash_from_operations"]
        - row["capital_expenditure"]
        - row["free_cash_flow"]
    )

    print(
        f"FY{int(row['fiscal_year'])}: "
        f"Cash reconciliation difference={cash_difference:.2f}, "
        f"FCF difference={fcf_difference:.2f}"
    )


print(f"\nSaved: {OUTPUT}")
