from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with open(
    "sql/analysis/002_peer_scorecard.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    sql = f.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Created analytics.vw_peer_scorecard")

query = text("""
SELECT
    symbol,
    revenue_cagr_4y_pct,
    pat_cagr_4y_pct,
    eps_cagr_4y_pct,
    fcf_cagr_4y_pct,
    ebitda_margin_pct,
    net_profit_margin_pct,
    roe_pct,
    roa_pct,
    fcf_conversion_pct,
    composite_rank_points,
    overall_peer_rank
FROM analytics.vw_peer_scorecard
ORDER BY overall_peer_rank, symbol;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\n" + "=" * 130)
print("FINSIGHT 360 — FY2026 PEER FINANCIAL SCORECARD")
print("=" * 130)

for r in rows:

    print(
        f"{r['symbol']:8s} | "
        f"Revenue CAGR={r['revenue_cagr_4y_pct']}% | "
        f"PAT CAGR={r['pat_cagr_4y_pct']}% | "
        f"EPS CAGR={r['eps_cagr_4y_pct']}% | "
        f"FCF CAGR={r['fcf_cagr_4y_pct']}% | "
        f"EBITDA Margin={r['ebitda_margin_pct']}% | "
        f"Net Margin={r['net_profit_margin_pct']}% | "
        f"ROE={r['roe_pct']}% | "
        f"ROA={r['roa_pct']}% | "
        f"FCF Conv={r['fcf_conversion_pct']}% | "
        f"Score={r['composite_rank_points']} | "
        f"Overall Rank={r['overall_peer_rank']}"
    )

print("\nPeer scorecard created successfully.")
