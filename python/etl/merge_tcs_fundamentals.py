from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

BASE = ROOT / "data/interim/financials/TCS"
OUTPUT = BASE / "TCS_fundamentals_FY2026_FY2025.csv"

pl = pd.read_csv(
    BASE / "parsed_profit_loss_FY2026_FY2025.csv"
)

bs = pd.read_csv(
    BASE / "parsed_balance_sheet_FY2026_FY2025.csv"
)

cf = pd.read_csv(
    BASE / "parsed_cash_flow_FY2026_FY2025.csv"
)

keys = ["company_code", "fiscal_year"]

df = (
    pl
    .merge(bs, on=keys, how="inner", validate="one_to_one")
    .merge(cf, on=keys, how="inner", validate="one_to_one")
)

# Core metadata
df["company_name"] = "Tata Consultancy Services"
df["period_end"] = pd.to_datetime(
    df["fiscal_year"].astype(str) + "-03-31"
)

df["statement_scope"] = "Consolidated"
df["currency"] = "INR"
df["unit"] = "INR Crore"
df["source_type"] = "Annual Report"
df["source_file"] = "TCS_Annual_Report_2025-26.pdf"
df["verification_status"] = "VERIFIED"

# Final validation flags
df["balance_sheet_valid"] = (
    (
        df["total_assets"]
        - df["total_equity_and_liabilities"]
    ).abs() < 0.01
)

df["cash_flow_valid"] = (
    (
        df["opening_cash"]
        + df["net_change_in_cash"]
        + df["fx_effect_on_cash"]
        - df["closing_cash"]
    ).abs() < 0.01
)

df["profit_valid"] = (
    (
        df["profit_before_tax"]
        - df["total_tax_expense"]
        - df["net_income"]
    ).abs() < 0.01
)

if not df[
    [
        "balance_sheet_valid",
        "cash_flow_valid",
        "profit_valid"
    ]
].all().all():

    raise ValueError(
        "One or more financial statement validations failed."
    )

# Useful analyst metrics
df["revenue_growth_yoy"] = df["revenue"].pct_change(-1)

df["ebitda_margin"] = (
    df["ebitda"] / df["revenue"]
)

df["net_profit_margin"] = (
    df["net_income"] / df["revenue"]
)

df["fcf_margin"] = (
    df["free_cash_flow"] / df["revenue"]
)

df["cfo_to_pat"] = (
    df["cash_from_operations"] / df["net_income"]
)

# Arrange newest fiscal year first
df = df.sort_values(
    "fiscal_year",
    ascending=False
).reset_index(drop=True)

df.to_csv(OUTPUT, index=False)

print("TCS three-statement merge complete")
print("=" * 88)

print(
    df[
        [
            "fiscal_year",
            "revenue",
            "ebitda",
            "net_income",
            "total_assets",
            "shareholders_equity",
            "cash_from_operations",
            "capital_expenditure",
            "free_cash_flow"
        ]
    ].to_string(index=False)
)

print("\nAnalyst metrics")
print("-" * 88)

display = df[
    [
        "fiscal_year",
        "revenue_growth_yoy",
        "ebitda_margin",
        "net_profit_margin",
        "fcf_margin",
        "cfo_to_pat"
    ]
].copy()

for col in [
    "revenue_growth_yoy",
    "ebitda_margin",
    "net_profit_margin",
    "fcf_margin"
]:
    display[col] = (display[col] * 100).round(2)

display["cfo_to_pat"] = display["cfo_to_pat"].round(2)

print(display.to_string(index=False))

print("\nValidation")
print("-" * 88)

print(
    df[
        [
            "fiscal_year",
            "profit_valid",
            "balance_sheet_valid",
            "cash_flow_valid",
            "verification_status"
        ]
    ].to_string(index=False)
)

print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved: {OUTPUT}")
