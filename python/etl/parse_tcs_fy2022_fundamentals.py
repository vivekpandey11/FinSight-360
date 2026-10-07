from pathlib import Path
import re
import pandas as pd

ROOT = Path.cwd()
BASE = ROOT / "data" / "interim" / "financials" / "TCS"

PL = BASE / "profit_loss_FY2023_FY2022.txt"
BS = BASE / "balance_sheet_FY2023_FY2022.txt"
CF = BASE / "cash_flow_FY2023_FY2022.txt"

for f in (PL, BS, CF):
    if not f.exists():
        raise FileNotFoundError(f)

def num(x):
    x = str(x).strip().replace(",", "").replace("₹", "").replace("`", "")
    if x in {"", "-", "–", "—"}:
        return 0.0
    if x.startswith("(") and x.endswith(")"):
        return -float(x[1:-1])
    return float(x)

# Source values independently extracted from the consolidated statements.
# FY2023 is retained here specifically as a reconciliation control for FY2022.
rows = [
    {
        "company_code": "TCS",
        "fiscal_year": 2023,
        "period_end": "2023-03-31",

        "revenue": 225458,
        "other_income": 3449,
        "total_income": 228907,

        "finance_cost": 779,
        "depreciation_amortization": 5022,
        "profit_before_tax": 56907,
        "current_tax": 14757,
        "deferred_tax": -153,
        "tax_expense": 14604,
        "net_income": 42303,
        "profit_attributable_shareholders": 42147,
        "eps": 115.19,

        "cash_and_equivalents": 7123,
        "receivables": 149 + 199 + 41049 + 8905,
        "current_assets": 110270,
        "property_plant_equipment": 10230,
        "total_assets": 143651,
        "payables": 10515,
        "current_liabilities": 43558,
        "total_liabilities": 8887 + 43558,
        "shareholders_equity": 90424,
        "total_equity": 91206,

        "cash_from_operations": 41965,
        "capital_expenditure": 2532 + 355,
        "cash_from_investing": 39,
        "cash_from_financing": -47878,
        "dividends_paid": -41347,
        "opening_cash": 12488,
        "fx_effect_cash": 509,
        "closing_cash": 7123,
    },

    {
        "company_code": "TCS",
        "fiscal_year": 2022,
        "period_end": "2022-03-31",

        "revenue": 191754,
        "other_income": 4018,
        "total_income": 195772,

        "finance_cost": 784,
        "depreciation_amortization": 4604,
        "profit_before_tax": 51687,
        "current_tax": 13654,
        "deferred_tax": -416,
        "tax_expense": 13238,
        "net_income": 38449,
        "profit_attributable_shareholders": 38327,
        "eps": 103.62,

        "cash_and_equivalents": 12488,
        "receivables": 145 + 55 + 34074 + 7736,
        "current_assets": 108310,
        "property_plant_equipment": 10774,
        "total_assets": 141514,
        "payables": 8045,
        "current_liabilities": 42351,
        "total_liabilities": 9317 + 42351,
        "shareholders_equity": 89139,
        "total_equity": 89846,

        "cash_from_operations": 39949,
        "capital_expenditure": 2483 + 497,
        "cash_from_investing": -897,
        "cash_from_financing": -33581,
        "dividends_paid": -13317,
        "opening_cash": 6858,
        "fx_effect_cash": 159,
        "closing_cash": 12488,
    },
]

df = pd.DataFrame(rows)

# Same analytical EBITDA methodology used for the existing TCS history:
# EBIT = PBT + finance cost
# EBITDA = EBIT + D&A
df["ebit"] = df["profit_before_tax"] + df["finance_cost"]
df["ebitda"] = df["ebit"] + df["depreciation_amortization"]

df["free_cash_flow"] = (
    df["cash_from_operations"] - df["capital_expenditure"]
)

# Validation controls
df["total_income_check"] = (
    df["revenue"] + df["other_income"] - df["total_income"]
)

df["pat_check"] = (
    df["profit_before_tax"] - df["tax_expense"] - df["net_income"]
)

df["balance_sheet_check"] = (
    df["total_assets"] -
    (df["total_equity"] + df["total_liabilities"])
)

df["cash_reconciliation_check"] = (
    df["opening_cash"]
    + df["cash_from_operations"]
    + df["cash_from_investing"]
    + df["cash_from_financing"]
    + df["fx_effect_cash"]
    - df["closing_cash"]
)

df["fcf_check"] = (
    df["cash_from_operations"]
    - df["capital_expenditure"]
    - df["free_cash_flow"]
)

checks = [
    "total_income_check",
    "pat_check",
    "balance_sheet_check",
    "cash_reconciliation_check",
    "fcf_check",
]

print("\n=== TCS FY2023 / FY2022 PARSED DATA ===")
print(
    df[
        [
            "fiscal_year",
            "revenue",
            "ebitda",
            "ebit",
            "profit_before_tax",
            "net_income",
            "eps",
            "cash_and_equivalents",
            "receivables",
            "total_assets",
            "shareholders_equity",
            "cash_from_operations",
            "capital_expenditure",
            "free_cash_flow",
        ]
    ].to_string(index=False)
)

print("\n=== VALIDATION ===")
print(df[["fiscal_year"] + checks].to_string(index=False))

for check in checks:
    if not (df[check].abs() < 0.01).all():
        raise ValueError(f"Validation failed: {check}")

# Reconcile FY2023 against the already locked FY2023 dataset.
old_file = BASE / "TCS_fundamentals_FY2024_FY2023.csv"

if not old_file.exists():
    raise FileNotFoundError(old_file)

old = pd.read_csv(old_file)
old23 = old.loc[old["fiscal_year"] == 2023].iloc[0]
new23 = df.loc[df["fiscal_year"] == 2023].iloc[0]

reconcile = {
    "revenue": old23["revenue"] - new23["revenue"],
    "ebitda": old23["ebitda"] - new23["ebitda"],
    "ebit": old23["ebit"] - new23["ebit"],
    "profit_before_tax":
        old23["profit_before_tax"] - new23["profit_before_tax"],
    "net_income":
        old23["net_income"] - new23["net_income"],
    "eps": old23["eps"] - new23["eps"],
    "cash_and_equivalents":
        old23["cash_and_equivalents"] - new23["cash_and_equivalents"],
    "receivables":
        old23["receivables"] - new23["receivables"],
    "total_assets":
        old23["total_assets"] - new23["total_assets"],
    "shareholders_equity":
        old23["shareholders_equity"] - new23["shareholders_equity"],
    "cash_from_operations":
        old23["cash_from_operations"] - new23["cash_from_operations"],
    "capital_expenditure":
        old23["capital_expenditure"] - new23["capital_expenditure"],
    "free_cash_flow":
        old23["free_cash_flow"] - new23["free_cash_flow"],
}

print("\n=== FY2023 CROSS-REPORT RECONCILIATION ===")

for metric, difference in reconcile.items():
    print(f"{metric:30s} difference = {difference:.2f}")
    if abs(difference) >= 0.01:
        raise ValueError(
            f"FY2023 reconciliation failed for {metric}: {difference}"
        )

output = BASE / "parsed_fundamentals_FY2023_FY2022.csv"
df.to_csv(output, index=False)

print(f"\nSAVED -> {output}")
print("\nALL VALIDATIONS PASSED.")
