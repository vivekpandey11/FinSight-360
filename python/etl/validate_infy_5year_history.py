from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

sql = text("""
SELECT
    fp.fiscal_year,
    fp.period_id,
    i.revenue,
    i.ebitda,
    i.ebit,
    i.profit_before_tax AS pbt,
    i.net_income,
    i.eps,
    b.cash_and_equivalents AS cash,
    b.receivables,
    b.total_assets,
    b.shareholders_equity,
    b.total_liabilities,
    cf.cash_from_operations AS cfo,
    cf.capital_expenditure AS capex,
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
WHERE c.symbol = 'INFY'
  AND fp.period_type = 'ANNUAL'
  AND fp.fiscal_year BETWEEN 2022 AND 2026
ORDER BY fp.fiscal_year;
""")

with engine.connect() as conn:
    rows = conn.execute(sql).mappings().all()

print("\n========== INFOSYS FINAL 5-YEAR DATABASE AUDIT ==========\n")

for r in rows:
    print(
        f"FY{r['fiscal_year']} | "
        f"period={r['period_id']} | "
        f"Revenue={r['revenue']} | "
        f"EBITDA={r['ebitda']} | "
        f"EBIT={r['ebit']} | "
        f"PBT={r['pbt']} | "
        f"PAT={r['net_income']} | "
        f"EPS={r['eps']} | "
        f"Cash={r['cash']} | "
        f"Receivables={r['receivables']} | "
        f"Assets={r['total_assets']} | "
        f"Equity={r['shareholders_equity']} | "
        f"Liabilities={r['total_liabilities']} | "
        f"CFO={r['cfo']} | "
        f"CapEx={r['capex']} | "
        f"FCF={r['fcf']}"
    )

print("\n========== VALIDATION ==========")

years = [int(r["fiscal_year"]) for r in rows]

assert years == [2022, 2023, 2024, 2025, 2026], \
    f"Fiscal-year problem: {years}"

print("5/5 fiscal years present")

assert len(years) == len(set(years))
print("No duplicate annual periods")

required = [
    "revenue",
    "ebitda",
    "ebit",
    "pbt",
    "net_income",
    "eps",
    "cash",
    "receivables",
    "total_assets",
    "shareholders_equity",
    "total_liabilities",
    "cfo",
    "capex",
    "fcf",
]

for r in rows:
    for col in required:
        assert r[col] is not None, \
            f"Missing {col} in FY{r['fiscal_year']}"

print("No missing core financial metrics")

for r in rows:
    expected = float(r["cfo"]) - float(r["capex"])
    actual = float(r["fcf"])

    assert abs(expected - actual) < 0.01, \
        f"FCF mismatch FY{r['fiscal_year']}"

print("FCF reconciliation passed for all years")

print("\nINFOSYS FY2022-FY2026 DATABASE AUDIT PASSED")
