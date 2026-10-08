import pandas as pd
from sqlalchemy import text
from utils.db import get_engine
from pathlib import Path

engine = get_engine()

query = text("""
SELECT
    fp.fiscal_year,

    i.revenue,
    i.ebitda,
    i.depreciation_amortization AS da,
    i.ebit,
    i.finance_cost,
    i.profit_before_tax AS pbt,
    i.tax_expense,
    i.net_income,
    i.eps,

    b.cash_and_equivalents AS cash,
    b.current_assets,
    b.total_assets,
    b.current_liabilities,
    b.total_liabilities,
    b.shareholders_equity,

    cf.cash_from_operations AS cfo,
    cf.capital_expenditure AS capex,
    cf.dividends_paid,
    cf.free_cash_flow AS fcf

FROM fundamentals.financial_periods fp

JOIN core.companies c
    ON c.company_id = fp.company_id

LEFT JOIN fundamentals.income_statements i
    ON i.period_id = fp.period_id

LEFT JOIN fundamentals.balance_sheets b
    ON b.period_id = fp.period_id

LEFT JOIN fundamentals.cash_flows cf
    ON cf.period_id = fp.period_id

WHERE c.symbol = 'TCS'
  AND fp.period_type = 'ANNUAL'
  AND fp.fiscal_year BETWEEN 2022 AND 2026

ORDER BY fp.fiscal_year;
""")

with engine.connect() as conn:
    df = pd.read_sql(query, conn)

# --------------------------------------------------
# Historical analytical drivers
# --------------------------------------------------

df["revenue_growth_pct"] = (
    df["revenue"].pct_change() * 100
)

df["ebitda_margin_pct"] = (
    df["ebitda"] / df["revenue"] * 100
)

df["ebit_margin_pct"] = (
    df["ebit"] / df["revenue"] * 100
)

df["net_margin_pct"] = (
    df["net_income"] / df["revenue"] * 100
)

df["tax_rate_pct"] = (
    df["tax_expense"] / df["pbt"] * 100
)

df["da_pct_revenue"] = (
    df["da"] / df["revenue"] * 100
)

df["capex_pct_revenue"] = (
    df["capex"] / df["revenue"] * 100
)

df["cfo_pct_revenue"] = (
    df["cfo"] / df["revenue"] * 100
)

df["fcf_margin_pct"] = (
    df["fcf"] / df["revenue"] * 100
)

df["current_ratio"] = (
    df["current_assets"]
    / df["current_liabilities"]
)

# --------------------------------------------------
# Historical CAGR
# --------------------------------------------------

first_revenue = df.iloc[0]["revenue"]
last_revenue = df.iloc[-1]["revenue"]

revenue_cagr = (
    (last_revenue / first_revenue) ** (1 / 4) - 1
) * 100

first_ebitda = df.iloc[0]["ebitda"]
last_ebitda = df.iloc[-1]["ebitda"]

ebitda_cagr = (
    (last_ebitda / first_ebitda) ** (1 / 4) - 1
) * 100

first_pat = df.iloc[0]["net_income"]
last_pat = df.iloc[-1]["net_income"]

pat_cagr = (
    (last_pat / first_pat) ** (1 / 4) - 1
) * 100

first_fcf = df.iloc[0]["fcf"]
last_fcf = df.iloc[-1]["fcf"]

fcf_cagr = (
    (last_fcf / first_fcf) ** (1 / 4) - 1
) * 100

# --------------------------------------------------
# Historical averages
# --------------------------------------------------

driver_summary = pd.DataFrame({
    "metric": [
        "Revenue CAGR",
        "EBITDA CAGR",
        "PAT CAGR",
        "FCF CAGR",
        "Average EBITDA Margin",
        "Average EBIT Margin",
        "Average Net Margin",
        "Average Tax Rate",
        "Average D&A % Revenue",
        "Average CapEx % Revenue",
        "Average CFO % Revenue",
        "Average FCF Margin"
    ],

    "value_pct": [
        revenue_cagr,
        ebitda_cagr,
        pat_cagr,
        fcf_cagr,
        df["ebitda_margin_pct"].mean(),
        df["ebit_margin_pct"].mean(),
        df["net_margin_pct"].mean(),
        df["tax_rate_pct"].mean(),
        df["da_pct_revenue"].mean(),
        df["capex_pct_revenue"].mean(),
        df["cfo_pct_revenue"].mean(),
        df["fcf_margin_pct"].mean()
    ]
})

# --------------------------------------------------
# Save outputs
# --------------------------------------------------

output_dir = Path(
    "results/tables"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

historical_path = (
    output_dir /
    "tcs_historical_financial_model_base.csv"
)

drivers_path = (
    output_dir /
    "tcs_historical_driver_summary.csv"
)

df.round(4).to_csv(
    historical_path,
    index=False
)

driver_summary["value_pct"] = (
    driver_summary["value_pct"].round(2)
)

driver_summary.to_csv(
    drivers_path,
    index=False
)

# --------------------------------------------------
# Print
# --------------------------------------------------

print("\n" + "=" * 115)
print("FINSIGHT 360 — TCS HISTORICAL MODEL BASE")
print("=" * 115)

display_cols = [
    "fiscal_year",
    "revenue",
    "revenue_growth_pct",
    "ebitda_margin_pct",
    "ebit_margin_pct",
    "net_margin_pct",
    "tax_rate_pct",
    "capex_pct_revenue",
    "fcf_margin_pct"
]

print(
    df[display_cols]
    .round(2)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("HISTORICAL DRIVER SUMMARY")
print("=" * 70)

print(
    driver_summary.to_string(
        index=False
    )
)

print(
    f"\nSaved -> {historical_path}"
)

print(
    f"Saved -> {drivers_path}"
)

print(
    "\nTCS historical financial-model base "
    "created successfully."
)
