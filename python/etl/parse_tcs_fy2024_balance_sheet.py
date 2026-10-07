import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data/interim/financials/TCS/balance_sheet_FY2024_FY2023.txt"
OUTPUT = ROOT / "data/interim/financials/TCS/parsed_balance_sheet_FY2024_FY2023.csv"

text = INPUT.read_text(encoding="utf-8")

def clean_num(x):
    x = x.replace(",", "").strip()
    if x in {"-", "?", "?"}:
        return 0.0
    if x.startswith("(") and x.endswith(")"):
        return -float(x[1:-1])
    return float(x)

def pair_between(start_label, end_label):
    start = text.lower().find(start_label.lower())
    if start == -1:
        raise ValueError(f"Could not find: {start_label}")

    end = text.lower().find(end_label.lower(), start)
    if end == -1:
        raise ValueError(f"Could not find: {end_label}")

    section = text[start:end]
    nums = []

    for line in section.splitlines()[1:]:
        line = line.strip()
        if re.fullmatch(r"\(?[\d,]+(?:\.\d+)?\)?", line):
            nums.append(clean_num(line))

    if len(nums) < 2:
        raise ValueError(f"Could not extract: {start_label}")

    return nums[-2], nums[-1]

ppe = pair_between(
    "Property, plant and equipment",
    "Capital work-in-progress"
)

cash = pair_between(
    "Cash and cash equivalents",
    "Other balances with banks"
)

current_assets = pair_between(
    "Total current assets",
    "TOTAL ASSETS"
)

total_assets = pair_between(
    "TOTAL ASSETS",
    "EQUITY AND LIABILITIES"
)

shareholders_equity = pair_between(
    "Equity attributable to shareholders of the Company",
    "Non-controlling interests"
)

total_equity = pair_between(
    "Total equity",
    "Liabilities"
)

noncurrent_liabilities = pair_between(
    "Total non-current liabilities",
    "Financial liabilities"
)

current_liabilities = pair_between(
    "Total current liabilities",
    "TOTAL EQUITY AND LIABILITIES"
)

total_equity_liabilities = pair_between(
    "TOTAL EQUITY AND LIABILITIES",
    "NOTES FORMING PART"
)

trade_payables = pair_between(
    "Trade payables",
    "Other financial liabilities"
)

# Same receivables methodology as FY25/FY26:
# billed + unbilled, current + non-current
receivables = (
    127 + 16 + 44434 + 9143,
    149 + 199 + 41049 + 8905
)

years = [2024, 2023]
rows = []

for i, year in enumerate(years):

    total_liabilities = (
        noncurrent_liabilities[i] +
        current_liabilities[i]
    )

    rows.append({
        "fiscal_year": year,
        "cash_and_equivalents": cash[i],
        "receivables": receivables[i],
        "current_assets": current_assets[i],
        "property_plant_equipment": ppe[i],
        "total_assets": total_assets[i],
        "trade_payables": trade_payables[i],
        "current_liabilities": current_liabilities[i],

        # Keep NULL until debt methodology is finalized
        "total_debt": None,

        "total_liabilities": total_liabilities,
        "shareholders_equity": shareholders_equity[i],
        "total_equity": total_equity[i],
        "total_equity_liabilities": total_equity_liabilities[i],
    })

df = pd.DataFrame(rows)

df["accounting_check"] = (
    df["total_assets"]
    - df["total_equity"]
    - df["total_liabilities"]
)

df["statement_check"] = (
    df["total_assets"]
    - df["total_equity_liabilities"]
)

print(df.to_string(index=False))

print("\nValidation:")

for _, r in df.iterrows():
    print(
        f"FY{int(r['fiscal_year'])}: "
        f"Assets-(Equity+Liabilities)={r['accounting_check']:.2f}, "
        f"Statement difference={r['statement_check']:.2f}"
    )

if not (
    (df["accounting_check"].abs() < 0.01).all()
    and
    (df["statement_check"].abs() < 0.01).all()
):
    raise ValueError("Balance Sheet validation failed")

df.to_csv(OUTPUT, index=False)

print(f"\nSaved: {OUTPUT}")
print("Balance Sheet validation PASSED.")

