from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

QUERY = text("""
SELECT
    c.symbol,
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
    b.current_assets,
    b.total_assets,
    b.current_liabilities,
    b.total_liabilities,
    b.shareholders_equity,

    cf.cash_from_operations AS cfo,
    cf.capital_expenditure AS capex,
    cf.cash_from_investing AS cfi,
    cf.cash_from_financing AS cff,
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

WHERE c.symbol IN ('TCS', 'INFY', 'HCLTECH')
  AND fp.period_type = 'ANNUAL'
  AND fp.fiscal_year BETWEEN 2022 AND 2026

ORDER BY c.symbol, fp.fiscal_year;
""")

with engine.connect() as conn:
    rows = conn.execute(QUERY).mappings().all()

print("\n" + "=" * 120)
print("FINSIGHT 360 — FINAL FUNDAMENTALS DATABASE AUDIT")
print("=" * 120)

for r in rows:

    print(
        f"{r['symbol']:8s} "
        f"FY{r['fiscal_year']} | "
        f"period={r['period_id']} | "
        f"Revenue={r['revenue']} | "
        f"EBITDA={r['ebitda']} | "
        f"PAT={r['net_income']} | "
        f"EPS={r['eps']} | "
        f"Assets={r['total_assets']} | "
        f"Equity={r['shareholders_equity']} | "
        f"CFO={r['cfo']} | "
        f"CapEx={r['capex']} | "
        f"FCF={r['fcf']}"
    )

print("\n" + "=" * 120)
print("STRUCTURAL VALIDATION")
print("=" * 120)

expected_companies = {"TCS", "INFY", "HCLTECH"}
expected_years = {2022, 2023, 2024, 2025, 2026}

symbols = {r["symbol"] for r in rows}

assert symbols == expected_companies, (
    f"Company mismatch: {symbols}"
)

print("PASS: All 3 companies present")

assert len(rows) == 15, (
    f"Expected 15 company-years, found {len(rows)}"
)

print("PASS: 15/15 annual company-periods present")

for symbol in expected_companies:

    company_rows = [
        r for r in rows
        if r["symbol"] == symbol
    ]

    years = {
        int(r["fiscal_year"])
        for r in company_rows
    }

    assert years == expected_years, (
        f"{symbol}: fiscal years incorrect -> {years}"
    )

    assert len(company_rows) == 5

    print(
        f"PASS: {symbol} FY2022-FY2026 complete"
    )

keys = [
    (r["symbol"], int(r["fiscal_year"]))
    for r in rows
]

assert len(keys) == len(set(keys))

print("PASS: No duplicate company-year periods")

print("\n" + "=" * 120)
print("ACCOUNTING / DATA QUALITY VALIDATION")
print("=" * 120)

# Metrics that must exist for every company-year.
universal_required = [
    "pbt",
    "net_income",
    "cash",
    "current_assets",
    "total_assets",
    "current_liabilities",
    "total_liabilities",
    "shareholders_equity",
    "cfo",
]

for r in rows:
    for metric in universal_required:

        assert r[metric] is not None, (
            f"Missing {metric}: "
            f"{r['symbol']} FY{r['fiscal_year']}"
        )

print("PASS: Universal core metrics populated")

# FCF reconciliation wherever CapEx exists.
for r in rows:

    if (
        r["cfo"] is not None
        and r["capex"] is not None
        and r["fcf"] is not None
    ):
        expected_fcf = (
            float(r["cfo"])
            - float(r["capex"])
        )

        assert abs(
            expected_fcf - float(r["fcf"])
        ) < 0.01, (
            f"FCF mismatch: "
            f"{r['symbol']} FY{r['fiscal_year']}"
        )

print("PASS: FCF reconciliation where source CapEx is available")

# HCLTech FY2024 extraction limitation.
hcl24 = next(
    r for r in rows
    if r["symbol"] == "HCLTECH"
    and int(r["fiscal_year"]) == 2024
)

known_hcl24_nulls = [
    "revenue",
    "ebitda",
    "ebit",
    "eps",
    "receivables",
    "capex",
    "cff",
    "dividends_paid",
    "fcf",
]

print("\nHCLTECH FY2024 documented extraction gaps:")

for metric in known_hcl24_nulls:
    status = (
        "NULL (expected)"
        if hcl24[metric] is None
        else f"AVAILABLE = {hcl24[metric]}"
    )

    print(
        f"  {metric:20s}: {status}"
    )

# Summary
print("\n" + "=" * 120)
print("FINAL STATUS")
print("=" * 120)

print("TCS      : 5/5 years loaded and audited")
print("INFY     : 5/5 years loaded and audited")
print("HCLTECH  : 5/5 years loaded")
print("HCLTECH FY2024: documented source-text extraction limitations")
print("")
print("TOTAL    : 15/15 annual company-periods in PostgreSQL")
print("")
print("FINSIGHT 360 FUNDAMENTALS INGESTION AUDIT PASSED")
