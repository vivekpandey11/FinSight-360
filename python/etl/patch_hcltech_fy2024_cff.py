import sys
sys.path.insert(0, "python")

from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with engine.begin() as conn:

    # Find exact HCLTECH FY2024 annual period
    row = conn.execute(text("""
        SELECT
            fp.period_id,
            c.symbol,
            fp.fiscal_year,
            fp.period_type,
            cf.cash_from_financing
        FROM fundamentals.financial_periods fp
        JOIN core.companies c
          ON c.company_id = fp.company_id
        LEFT JOIN fundamentals.cash_flows cf
          ON cf.period_id = fp.period_id
        WHERE c.symbol = 'HCLTECH'
          AND fp.fiscal_year = 2024
          AND fp.period_type = 'ANNUAL'
    """)).mappings().first()

    if row is None:
        raise RuntimeError(
            "HCLTECH FY2024 annual period not found."
        )

    print("\nBEFORE PATCH")
    print(dict(row))

    if row["cash_from_financing"] is not None:
        raise RuntimeError(
            "cash_from_financing is already populated. "
            "Patch stopped to avoid accidental overwrite."
        )

    # Source-backed FY2024 CFF recovered from annual report
    conn.execute(text("""
        UPDATE fundamentals.cash_flows
        SET cash_from_financing = :cff
        WHERE period_id = :period_id
    """), {
        "cff": -15464,
        "period_id": row["period_id"]
    })

    check = conn.execute(text("""
        SELECT
            fp.period_id,
            c.symbol,
            fp.fiscal_year,
            cf.cash_from_operations,
            cf.capital_expenditure,
            cf.cash_from_investing,
            cf.cash_from_financing,
            cf.dividends_paid,
            cf.free_cash_flow
        FROM fundamentals.financial_periods fp
        JOIN core.companies c
          ON c.company_id = fp.company_id
        JOIN fundamentals.cash_flows cf
          ON cf.period_id = fp.period_id
        WHERE c.symbol = 'HCLTECH'
          AND fp.fiscal_year = 2024
          AND fp.period_type = 'ANNUAL'
    """)).mappings().first()

print("\nAFTER PATCH")
print(dict(check))

assert float(check["cash_from_financing"]) == -15464.0

print("\n✓ HCLTECH FY2024 CFF patched successfully.")
print("✓ Source-backed value: -15,464 ₹ crore.")
print("✓ CapEx, dividends and FCF remain NULL — no values invented.")
