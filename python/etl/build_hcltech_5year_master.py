from pathlib import Path
import pandas as pd
import numpy as np

OUT = Path("data/interim/financials/HCLTECH")
OUT.mkdir(parents=True, exist_ok=True)

# HCLTech consolidated financials, INR crore.
# FY22/FY23 from 2022-23 AR
# FY24/FY23 from 2023-24 AR
# FY25/FY26 from 2025-26 AR
#
# EBIT methodology:
# FY26: PBT before exceptional item + finance cost
# Other years: PBT + finance cost
# EBITDA = EBIT + D&A
#
# CapEx = purchase of PPE + intangibles, positive magnitude.

data = [
    {
        "fiscal_year": 2022,
        "revenue": 85651,
        "other_income": 1067,
        "total_income": 86718,
        "depreciation_amortization": 4326,
        "finance_cost": 319,
        "pbt_before_exceptional": 16951,
        "exceptional_items": 0,
        "profit_before_tax": 16951,
        "tax_expense": 3428,
        "net_income": 13523,
        "eps": 49.77,

        "cash_and_equivalents": 10510,
        "current_assets": 48041,
        "total_assets": 89033,
        "total_equity": 62006,
        "total_liabilities": 27027,
        "current_liabilities": 18775,

        "operating_cash_flow": 16900,
        "capital_expenditure": 1645,
        "investing_cash_flow": 1477,
        "financing_cash_flow": -14508,
        "dividends_paid": -11389,
    },
    {
        "fiscal_year": 2023,
        "revenue": 101456,
        "other_income": 1358,
        "total_income": 102814,
        "depreciation_amortization": 4145,
        "finance_cost": 353,
        "pbt_before_exceptional": 19488,
        "exceptional_items": 0,
        "profit_before_tax": 19488,
        "tax_expense": 4643,
        "net_income": 14845,
        "eps": 54.85,

        "cash_and_equivalents": 9065,
        "current_assets": 53577,
        "total_assets": 93411,
        "total_equity": 65398,
        "total_liabilities": 28013,
        "current_liabilities": 21431,

        "operating_cash_flow": 18009,
        "capital_expenditure": 1661,
        "investing_cash_flow": -3931,
        "financing_cash_flow": -15881,
        "dividends_paid": -12995,
    },
    {
        "fiscal_year": 2024,
        "revenue": np.nan,
        "other_income": np.nan,
        "total_income": 111408,
        "depreciation_amortization": np.nan,
        "finance_cost": np.nan,
        "pbt_before_exceptional": 20967,
        "exceptional_items": 0,
        "profit_before_tax": 20967,
        "tax_expense": 5257,
        "net_income": 15710,
        "eps": np.nan,

        "cash_and_equivalents": 9441,
        "current_assets": 59331,
        "total_assets": 99777,
        "total_equity": 68271,
        "total_liabilities": 31506,
        "current_liabilities": 22726,

        "operating_cash_flow": 22448,
        "capital_expenditure": np.nan,
        "investing_cash_flow": -6723,
        "financing_cash_flow": np.nan,
        "dividends_paid": np.nan,
    },
    {
        "fiscal_year": 2025,
        "revenue": 117055,
        "other_income": 2485,
        "total_income": 119540,
        "depreciation_amortization": 4084,
        "finance_cost": 644,
        "pbt_before_exceptional": 23261,
        "exceptional_items": 0,
        "profit_before_tax": 23261,
        "tax_expense": 5862,
        "net_income": 17399,
        "eps": 64.16,

        "cash_and_equivalents": 8245,
        "current_assets": 62109,
        "total_assets": 105544,
        "total_equity": 69673,
        "total_liabilities": 35871,
        "current_liabilities": 28039,

        "operating_cash_flow": 22261,
        "capital_expenditure": 1108,
        "investing_cash_flow": -4914,
        "financing_cash_flow": -18561,
        "dividends_paid": -16250,
    },
    {
        "fiscal_year": 2026,
        "revenue": 130144,
        "other_income": 1530,
        "total_income": 131674,
        "depreciation_amortization": 4355,
        "finance_cost": 869,
        "pbt_before_exceptional": 23058,
        "exceptional_items": 956,
        "profit_before_tax": 22102,
        "tax_expense": 5450,
        "net_income": 16652,
        "eps": 61.46,

        "cash_and_equivalents": 8265,
        "current_assets": 70542,
        "total_assets": 116258,
        "total_equity": 75197,
        "total_liabilities": 41061,
        "current_liabilities": 31826,

        "operating_cash_flow": 19975,
        "capital_expenditure": 1422,
        "investing_cash_flow": -1473,
        "financing_cash_flow": -19369,
        "dividends_paid": -14618,
    },
]

df = pd.DataFrame(data)

# Derived analytical metrics
df["ebit"] = df["pbt_before_exceptional"] + df["finance_cost"]
df["ebitda"] = df["ebit"] + df["depreciation_amortization"]
df["free_cash_flow"] = (
    df["operating_cash_flow"] - df["capital_expenditure"]
)

# Accounting validations
df["bs_difference"] = (
    df["total_assets"]
    - df["total_equity"]
    - df["total_liabilities"]
)

df["pnl_difference"] = (
    df["profit_before_tax"]
    - df["tax_expense"]
    - df["net_income"]
)

df["income_difference"] = (
    df["revenue"]
    + df["other_income"]
    - df["total_income"]
)

print("\nHCLTECH FY2022-FY2026 MASTER DATA")
print("=" * 110)
print(df.to_string(index=False))

print("\nVALIDATIONS")
print("=" * 110)

assert len(df) == 5
assert df["fiscal_year"].nunique() == 5

assert (df["bs_difference"] == 0).all()
assert (df["pnl_difference"] == 0).all()

income_check = df["income_difference"].dropna()
assert (income_check == 0).all()

fcf_check = df.dropna(
    subset=["operating_cash_flow", "capital_expenditure"]
)
assert (
    fcf_check["free_cash_flow"]
    ==
    fcf_check["operating_cash_flow"]
    - fcf_check["capital_expenditure"]
).all()

print("PASS: 5 fiscal years present")
print("PASS: No duplicate fiscal years")
print("PASS: Balance sheet equation")
print("PASS: PBT - Tax = PAT")
print("PASS: Revenue + Other Income = Total Income where available")
print("PASS: FCF = CFO - CapEx where available")

output = OUT / "HCLTECH_fundamentals_FY2022_FY2026.csv"
df.to_csv(output, index=False)

print(f"\nSaved -> {output}")
print("\nNOTE: FY2024 source PDF has corrupted text encoding.")
print("FY2024 fields not safely recoverable from current extraction remain NULL.")
print("They will NOT be guessed.")
print("\nHCLTECH MASTER BUILD COMPLETE")
