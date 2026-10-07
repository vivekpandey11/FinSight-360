import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data/interim/financials/TCS/cash_flow_FY2024_FY2023.txt"
OUTPUT = ROOT / "data/interim/financials/TCS/parsed_cash_flow_FY2024_FY2023.csv"

text = INPUT.read_text(encoding="utf-8")

def clean_num(x):
    x = x.replace(",", "").strip()
    if x in {"-", "?", "?"}:
        return 0.0
    if x.startswith("(") and x.endswith(")"):
        return -float(x[1:-1])
    return float(x)

def pair_after(label):
    start = text.lower().find(label.lower())

    if start == -1:
        raise ValueError(f"Could not find: {label}")

    lines = text[start:].splitlines()[1:]
    values = []

    for line in lines:
        line = line.strip()

        if re.fullmatch(r"-|\(?[\d,]+(?:\.\d+)?\)?", line):
            values.append(clean_num(line))

        if len(values) == 2:
            return values[0], values[1]

    raise ValueError(f"Could not extract values: {label}")


cfo = pair_after(
    "Net cash generated from operating activities"
)

ppe_purchase = pair_after(
    "Payment for purchase of property, plant and equipment"
)

intangible_purchase = pair_after(
    "Payment for purchase of intangible assets"
)

cfi = pair_after(
    "Net cash generated from investing activities"
)

cff = pair_after(
    "Net cash used in financing activities"
)

dividends = pair_after(
    "Dividend paid"
)

net_change_cash = pair_after(
    "Net change in cash and cash equivalents"
)

opening_cash = pair_after(
    "Cash and cash equivalents at the beginning of the year"
)

fx_effect = pair_after(
    "Exchange difference on translation of foreign currency cash and cash equivalents"
)

closing_cash = pair_after(
    "Cash and cash equivalents at the end of the year"
)

years = [2024, 2023]
rows = []

for i, year in enumerate(years):

    # Source reports purchases as negative cash flows.
    # FinSight stores CapEx as positive analytical magnitude.
    capex = abs(ppe_purchase[i]) + abs(intangible_purchase[i])

    free_cash_flow = cfo[i] - capex

    cash_reconciliation = (
        opening_cash[i]
        + net_change_cash[i]
        + fx_effect[i]
        - closing_cash[i]
    )

    rows.append({
        "fiscal_year": year,
        "cash_from_operations": cfo[i],
        "ppe_purchase": ppe_purchase[i],
        "intangible_purchase": intangible_purchase[i],
        "capital_expenditure": capex,
        "cash_from_investing": cfi[i],
        "cash_from_financing": cff[i],
        "dividends_paid": dividends[i],
        "free_cash_flow": free_cash_flow,
        "net_change_cash": net_change_cash[i],
        "opening_cash": opening_cash[i],
        "fx_effect": fx_effect[i],
        "closing_cash": closing_cash[i],
        "cash_reconciliation_check": cash_reconciliation
    })

df = pd.DataFrame(rows)

df["fcf_check"] = (
    df["cash_from_operations"]
    - df["capital_expenditure"]
    - df["free_cash_flow"]
)

print(df.to_string(index=False))

print("\nValidation:")

for _, r in df.iterrows():
    print(
        f"FY{int(r['fiscal_year'])}: "
        f"Cash reconciliation={r['cash_reconciliation_check']:.2f}, "
        f"FCF difference={r['fcf_check']:.2f}"
    )

if not (
    (df["cash_reconciliation_check"].abs() < 0.01).all()
    and
    (df["fcf_check"].abs() < 0.01).all()
):
    raise ValueError("Cash Flow validation failed")

df.to_csv(OUTPUT, index=False)

print(f"\nSaved: {OUTPUT}")
print("Cash Flow validation PASSED.")
