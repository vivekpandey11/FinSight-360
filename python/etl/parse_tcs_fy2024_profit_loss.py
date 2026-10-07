import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/interim/financials/TCS/profit_loss_FY2024_FY2023.txt"
OUTPUT = ROOT / "data/interim/financials/TCS/parsed_profit_loss_FY2024_FY2023.csv"

text = INPUT.read_text(encoding="utf-8")

def clean_num(x):
    x = x.replace(",", "").strip()
    if x in {"-", "?", "?"}:
        return 0.0
    if x.startswith("(") and x.endswith(")"):
        return -float(x[1:-1])
    return float(x)

def values_after_label(label, has_note=True):
    pos = text.lower().find(label.lower())

    if pos == -1:
        raise ValueError(f"Could not find: {label}")

    section = text[pos:].splitlines()

    values = []

    # First line contains label itself, so start after it.
    for line in section[1:]:
        line = line.strip()

        if not line:
            continue

        # Accept only lines that consist entirely of a number.
        if re.fullmatch(r"\(?[\d,]+(?:\.\d+)?\)?", line):
            values.append(clean_num(line))

        # Note number comes first for fields such as Revenue / Finance costs.
        required = 3 if has_note else 2

        if len(values) >= required:
            break

    if has_note:
        if len(values) < 3:
            raise ValueError(f"Not enough values for: {label}")
        return values[1], values[2]

    if len(values) < 2:
        raise ValueError(f"Not enough values for: {label}")

    return values[0], values[1]


revenue = values_after_label("Revenue from operations", True)
other_income = values_after_label("Other income", True)
total_income = values_after_label("TOTAL INCOME", False)

finance_cost = values_after_label("Finance costs", True)
da = values_after_label("Depreciation and amortisation expense", False)

pbeit = values_after_label(
    "PROFIT BEFORE EXCEPTIONAL ITEM AND TAX",
    False
)

pbt = values_after_label("PROFIT BEFORE TAX", False)

current_tax = values_after_label("Current tax", True)
deferred_tax = values_after_label("Deferred tax", True)
total_tax = values_after_label("TOTAL TAX EXPENSE", False)
pat = values_after_label("PROFIT FOR THE YEAR", False)

# EPS has note 18 followed by FY24 and FY23 values.
eps = values_after_label(
    "Earnings per equity share:- Basic and diluted",
    True
)

years = [2024, 2023]
rows = []

for i, year in enumerate(years):

    # FinSight analytical definition:
    # EBIT = PBT before exceptional item + finance cost
    # EBITDA = EBIT + D&A
    ebit = pbeit[i] + finance_cost[i]
    ebitda = ebit + da[i]

    rows.append({
        "fiscal_year": year,
        "revenue": revenue[i],
        "other_income": other_income[i],
        "total_income": total_income[i],
        "finance_cost": finance_cost[i],
        "depreciation_amortization": da[i],
        "profit_before_exceptional_items_tax": pbeit[i],
        "ebit": ebit,
        "ebitda": ebitda,
        "profit_before_tax": pbt[i],
        "current_tax": current_tax[i],
        "deferred_tax": deferred_tax[i],
        "total_tax_expense": total_tax[i],
        "net_income": pat[i],
        "eps": eps[i],
    })

df = pd.DataFrame(rows)

df["total_income_check"] = (
    df["revenue"]
    + df["other_income"]
    - df["total_income"]
)

df["pat_check"] = (
    df["profit_before_tax"]
    - df["total_tax_expense"]
    - df["net_income"]
)

print(df.to_string(index=False))

print("\nValidation:")

for _, r in df.iterrows():
    print(
        f"FY{int(r['fiscal_year'])}: "
        f"Total income difference={r['total_income_check']:.2f}, "
        f"PAT difference={r['pat_check']:.2f}"
    )

if not (
    (df["total_income_check"].abs() < 0.01).all()
    and
    (df["pat_check"].abs() < 0.01).all()
):
    raise ValueError("P&L validation failed")

df.to_csv(OUTPUT, index=False)

print(f"\nSaved: {OUTPUT}")
print("P&L validation PASSED.")
