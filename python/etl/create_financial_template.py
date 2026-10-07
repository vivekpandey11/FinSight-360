import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sources = pd.read_csv(
    ROOT / "config" / "sources" / "financial_sources.csv"
)

columns = [
    "company_code",
    "fiscal_year",
    "period_end",
    "revenue",
    "operating_expenses",
    "ebitda",
    "depreciation_amortization",
    "ebit",
    "finance_cost",
    "profit_before_tax",
    "tax_expense",
    "net_income",
    "eps",
    "cash_and_equivalents",
    "receivables",
    "current_assets",
    "property_plant_equipment",
    "total_assets",
    "payables",
    "current_liabilities",
    "total_debt",
    "total_liabilities",
    "shareholders_equity",
    "cash_from_operations",
    "capital_expenditure",
    "cash_from_investing",
    "cash_from_financing",
    "dividends_paid",
    "free_cash_flow",
    "source_url",
    "verification_status"
]

df = sources[
    ["company_code", "fiscal_year", "period_end"]
].copy()

for column in columns[3:]:
    df[column] = ""

output = (
    ROOT
    / "data"
    / "interim"
    / "financials"
    / "financial_fundamentals_template.csv"
)

df.to_csv(output, index=False)

print("Financial template created")
print(f"Rows    : {len(df)}")
print(f"Columns : {len(df.columns)}")
print(f"File    : {output}")
print()
print(df[["company_code", "fiscal_year", "period_end"]].to_string(index=False))
