from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with open(
    "sql/analysis/003_dupont_analysis.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    sql = f.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Created analytics.vw_dupont_analysis")

query = text("""
SELECT
    symbol,
    fiscal_year,
    owner_net_profit_margin_pct,
    asset_turnover,
    equity_multiplier,
    dupont_roe_pct,
    direct_roe_pct
FROM analytics.vw_dupont_analysis
ORDER BY symbol, fiscal_year;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\n" + "=" * 115)
print("FINSIGHT 360 — DUPONT ANALYSIS")
print("=" * 115)

for r in rows:

    print(
        f"{r['symbol']:8s} FY{r['fiscal_year']} | "
        f"Owner Net Margin={r['owner_net_profit_margin_pct']}% | "
        f"Asset Turnover={r['asset_turnover']}x | "
        f"Equity Multiplier={r['equity_multiplier']}x | "
        f"DuPont ROE={r['dupont_roe_pct']}% | "
        f"Direct ROE={r['direct_roe_pct']}%"
    )

# Validation:
# DuPont ROE must reconcile with directly calculated ROE.

checked = 0

for r in rows:

    if (
        r["dupont_roe_pct"] is not None
        and r["direct_roe_pct"] is not None
    ):

        diff = abs(
            float(r["dupont_roe_pct"])
            - float(r["direct_roe_pct"])
        )

        assert diff <= 0.02, (
            f"DuPont reconciliation failed: "
            f"{r['symbol']} FY{r['fiscal_year']} "
            f"diff={diff}"
        )

        checked += 1

print("\n" + "=" * 115)
print("VALIDATION")
print("=" * 115)

print(
    f"PASS: DuPont ROE reconciled with direct ROE "
    f"for {checked} company-years"
)

print("\nDuPont analytics created successfully.")

