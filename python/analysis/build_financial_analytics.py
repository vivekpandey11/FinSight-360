from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

sql_file = "sql/analysis/001_financial_performance_view.sql"

with open(sql_file, "r", encoding="utf-8-sig") as f:
    view_sql = f.read()

with engine.begin() as conn:
    conn.execute(text(view_sql))

print("Created analytics.vw_financial_performance")

query = text("""
SELECT
    symbol,
    fiscal_year,
    revenue,
    revenue_yoy_pct,
    ebitda_margin_pct,
    net_profit_margin_pct,
    roe_pct,
    roa_pct,
    current_ratio,
    cfo_to_pat,
    fcf_conversion_pct
FROM analytics.vw_financial_performance
ORDER BY symbol, fiscal_year;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\n" + "=" * 125)
print("FINSIGHT 360 — FINANCIAL PERFORMANCE ANALYTICS")
print("=" * 125)

for r in rows:
    print(
        f"{r['symbol']:8s} FY{r['fiscal_year']} | "
        f"Revenue={r['revenue']} | "
        f"YoY={r['revenue_yoy_pct']}% | "
        f"EBITDA Margin={r['ebitda_margin_pct']}% | "
        f"Net Margin={r['net_profit_margin_pct']}% | "
        f"ROE={r['roe_pct']}% | "
        f"ROA={r['roa_pct']}% | "
        f"Current={r['current_ratio']} | "
        f"CFO/PAT={r['cfo_to_pat']} | "
        f"FCF Conversion={r['fcf_conversion_pct']}%"
    )

print("\nFinancial analytics view created successfully.")
