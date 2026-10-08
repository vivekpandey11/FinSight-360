from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

query = text("""
WITH latest_price AS (
    SELECT DISTINCT ON (c.symbol)
        c.company_id,
        c.symbol,
        mp.trade_date,
        mp.close_price
    FROM core.companies c
    JOIN market.market_prices mp
        ON mp.company_id = c.company_id
    WHERE c.symbol IN ('TCS', 'INFY', 'HCLTECH')
    ORDER BY
        c.symbol,
        mp.trade_date DESC
)
SELECT
    c.symbol,
    fp.fiscal_year,
    lp.trade_date,
    lp.close_price,
    i.revenue,
    i.ebitda,
    i.ebit,
    i.net_income,
    i.eps,
    b.cash_and_equivalents,
    b.total_debt,
    b.total_assets,
    b.shareholders_equity,
    cf.free_cash_flow
FROM core.companies c
JOIN fundamentals.financial_periods fp
    ON fp.company_id = c.company_id
JOIN fundamentals.income_statements i
    ON i.period_id = fp.period_id
JOIN fundamentals.balance_sheets b
    ON b.period_id = fp.period_id
JOIN fundamentals.cash_flows cf
    ON cf.period_id = fp.period_id
JOIN latest_price lp
    ON lp.company_id = c.company_id
WHERE
    c.symbol IN ('TCS', 'INFY', 'HCLTECH')
    AND fp.period_type = 'ANNUAL'
    AND fp.fiscal_year = 2026
ORDER BY c.symbol;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\n" + "=" * 125)
print("FINSIGHT 360 — FY2026 RELATIVE VALUATION INPUT AUDIT")
print("=" * 125)

for r in rows:
    print(f"""
{r['symbol']}
{'-' * 55}
Market Date       : {r['trade_date']}
Close Price       : {r['close_price']}
Revenue           : {r['revenue']}
EBITDA            : {r['ebitda']}
EBIT              : {r['ebit']}
Net Income        : {r['net_income']}
EPS               : {r['eps']}
Cash              : {r['cash_and_equivalents']}
Total Debt        : {r['total_debt']}
Total Assets      : {r['total_assets']}
Shareholders Eq.  : {r['shareholders_equity']}
Free Cash Flow    : {r['free_cash_flow']}
""")

print("=" * 125)

print(f"\nCompanies returned: {len(rows)}")

assert len(rows) == 3

for r in rows:
    assert r["close_price"] is not None
    assert r["revenue"] is not None
    assert r["ebitda"] is not None
    assert r["net_income"] is not None
    assert r["eps"] is not None

print("Core relative-valuation inputs validated successfully.")
