from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "data/interim/financials/TCS"

pl = pd.read_csv(DIR / "parsed_profit_loss_FY2024_FY2023.csv")
bs = pd.read_csv(DIR / "parsed_balance_sheet_FY2024_FY2023.csv")
cf = pd.read_csv(DIR / "parsed_cash_flow_FY2024_FY2023.csv")

# Merge one-to-one to prevent accidental duplicate years
df = (
    pl.merge(bs, on="fiscal_year", validate="one_to_one")
      .merge(cf, on="fiscal_year", validate="one_to_one")
)

# Metadata / lineage
df.insert(0, "company_code", "TCS")
df.insert(1, "company_name", "Tata Consultancy Services")

df["period_end"] = pd.to_datetime(
    df["fiscal_year"].astype(str) + "-03-31"
)

df["statement_scope"] = "Consolidated"
df["currency"] = "INR"
df["unit"] = "INR Crore"
df["source_type"] = "Annual Report"
df["source_file"] = "TCS_Annual_Report_2023-24.pdf"
df["verification_status"] = "VERIFIED"

# Analyst metrics
df["revenue_growth_pct"] = (
    df.sort_values("fiscal_year")["revenue"]
      .pct_change()
      .mul(100)
)

df["ebitda_margin_pct"] = (
    df["ebitda"] / df["revenue"] * 100
)

df["net_profit_margin_pct"] = (
    df["net_income"] / df["revenue"] * 100
)

df["fcf_margin_pct"] = (
    df["free_cash_flow"] / df["revenue"] * 100
)

df["cfo_pat_ratio"] = (
    df["cash_from_operations"] / df["net_income"]
)

# Final validation
required_years = {2023, 2024}

if set(df["fiscal_year"]) != required_years:
    raise ValueError(
        f"Unexpected fiscal years: {set(df['fiscal_year'])}"
    )

checks = [
    "total_income_check",
    "pat_check",
    "accounting_check",
    "statement_check",
    "cash_reconciliation_check",
    "fcf_check",
]

for col in checks:
    if not (df[col].abs() < 0.01).all():
        raise ValueError(f"Validation failed: {col}")

df = df.sort_values("fiscal_year", ascending=False)

OUTPUT = DIR / "TCS_fundamentals_FY2024_FY2023.csv"
df.to_csv(OUTPUT, index=False)

display_cols = [
    "fiscal_year",
    "revenue",
    "revenue_growth_pct",
    "ebitda",
    "ebitda_margin_pct",
    "net_income",
    "net_profit_margin_pct",
    "cash_from_operations",
    "capital_expenditure",
    "free_cash_flow",
    "fcf_margin_pct",
    "total_assets",
    "shareholders_equity",
]

print(df[display_cols].to_string(index=False))

print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved: {OUTPUT}")
print("TCS FY2024/FY2023 master fundamentals validation PASSED.")
