import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

# --------------------------------------------------
# Create downside-risk SQL view
# --------------------------------------------------

with open(
    "sql/analysis/006_downside_risk.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    sql = f.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Created analytics.vw_downside_risk")

# --------------------------------------------------
# Read downside-risk metrics
# --------------------------------------------------

risk_query = text("""
SELECT
    symbol,
    observations,
    annualized_downside_deviation_pct,
    sortino_zero_rf,
    historical_var_95_daily_pct,
    historical_cvar_95_daily_pct
FROM analytics.vw_downside_risk
ORDER BY symbol;
""")

with engine.connect() as conn:
    risk_rows = conn.execute(
        risk_query
    ).mappings().all()

print("\n" + "=" * 120)
print("FINSIGHT 360 — DOWNSIDE RISK")
print("=" * 120)

for r in risk_rows:

    print(
        f"{r['symbol']:10s} | "
        f"N={r['observations']} | "
        f"Downside Vol={r['annualized_downside_deviation_pct']}% | "
        f"Sortino(0% RF)={r['sortino_zero_rf']} | "
        f"Daily VaR95={r['historical_var_95_daily_pct']}% | "
        f"Daily CVaR95={r['historical_cvar_95_daily_pct']}%"
    )

# --------------------------------------------------
# Correlation matrix
# --------------------------------------------------

returns_query = text("""
SELECT
    trade_date,
    symbol,
    daily_return_pct
FROM analytics.vw_daily_market_analytics
WHERE daily_return_pct IS NOT NULL
ORDER BY trade_date, symbol;
""")

with engine.connect() as conn:
    df = pd.read_sql(
        returns_query,
        conn
    )

matrix = (
    df.pivot(
        index="trade_date",
        columns="symbol",
        values="daily_return_pct"
    )
    .corr()
    .round(4)
)

output_path = (
    "results/tables/"
    "market_return_correlation_matrix.csv"
)

matrix.to_csv(output_path)

print("\n" + "=" * 120)
print("RETURN CORRELATION MATRIX")
print("=" * 120)

print(matrix.to_string())

print(
    f"\nSaved correlation matrix -> "
    f"{output_path}"
)

print(
    "\nDownside risk and correlation "
    "analytics completed successfully."
)
