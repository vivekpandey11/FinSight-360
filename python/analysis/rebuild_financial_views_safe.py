from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with open(
    "sql/analysis/001_financial_performance_view.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    financial_sql = f.read()

with open(
    "sql/analysis/002_peer_scorecard.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    peer_sql = f.read()

print("=== SAFE ANALYTICS VIEW REBUILD ===")

try:
    with engine.begin() as conn:

        print("1. Dropping dependent peer scorecard view...")
        conn.execute(
            text(
                "DROP VIEW IF EXISTS "
                "analytics.vw_peer_scorecard"
            )
        )

        print("2. Dropping financial performance view...")
        conn.execute(
            text(
                "DROP VIEW IF EXISTS "
                "analytics.vw_financial_performance"
            )
        )

        print("3. Recreating financial performance view...")
        conn.execute(text(financial_sql))

        print("4. Recreating peer scorecard view...")
        conn.execute(text(peer_sql))

    print("✓ Atomic rebuild committed successfully.")

except Exception:
    print("✗ Rebuild failed — transaction rolled back.")
    raise


validation_sql = text("""
SELECT
    symbol,
    fiscal_year,
    net_income AS consolidated_pat,
    profit_attributable_to_owners AS owner_pat,
    net_profit_margin_pct AS consolidated_net_margin_pct,
    owner_pat_margin_pct,
    equity_attributable_to_owners AS owner_equity,
    non_controlling_interest,
    roe_pct,
    roa_pct
FROM analytics.vw_financial_performance
WHERE fiscal_year IN (2024, 2025, 2026)
ORDER BY symbol, fiscal_year;
""")

with engine.connect() as conn:
    rows = conn.execute(validation_sql).mappings().all()

print("\n=== FINANCIAL PERFORMANCE VALIDATION ===")

for r in rows:
    print(dict(r))


peer_sql_check = text("""
SELECT
    symbol,
    revenue_cagr_4y_pct,
    pat_cagr_4y_pct,
    eps_cagr_4y_pct,
    owner_pat_margin_pct,
    roe_pct,
    roa_pct,
    composite_rank_points,
    overall_peer_rank
FROM analytics.vw_peer_scorecard
ORDER BY overall_peer_rank, symbol;
""")

with engine.connect() as conn:
    rows = conn.execute(peer_sql_check).mappings().all()

print("\n=== PEER SCORECARD VALIDATION ===")

for r in rows:
    print(dict(r))

print("\n✓ Financial performance + peer scorecard validation completed.")
