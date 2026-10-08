from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with open(
    "sql/analysis/005_market_risk_metrics.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    sql = f.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Created analytics.vw_market_risk_metrics")

query = text("""
SELECT
    symbol,
    return_observations,
    paired_observations,
    annualized_return_pct,
    annualized_volatility_pct,
    beta_vs_nifty50,
    correlation_vs_nifty50,
    annualized_alpha_pct,
    sharpe_zero_rf
FROM analytics.vw_market_risk_metrics
ORDER BY symbol;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\n" + "=" * 145)
print("FINSIGHT 360 — MARKET RISK / RETURN METRICS")
print("=" * 145)

for r in rows:
    print(
        f"{r['symbol']:10s} | "
        f"N={r['return_observations']} | "
        f"Ann.Return={r['annualized_return_pct']}% | "
        f"Ann.Vol={r['annualized_volatility_pct']}% | "
        f"Beta={r['beta_vs_nifty50']} | "
        f"Corr={r['correlation_vs_nifty50']} | "
        f"Alpha={r['annualized_alpha_pct']}% | "
        f"Sharpe(0% RF)={r['sharpe_zero_rf']}"
    )

print("\nMarket risk metrics created successfully.")
