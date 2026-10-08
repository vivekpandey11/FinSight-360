from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

query = text("""
SELECT
    c.symbol,
    fp.fiscal_year,
    b.cash_and_equivalents,
    b.receivables,
    b.current_assets,
    b.property_plant_equipment,
    b.total_assets,
    b.payables,
    b.current_liabilities,
    b.total_debt,
    b.total_liabilities,
    b.shareholders_equity
FROM fundamentals.financial_periods fp

JOIN core.companies c
    ON c.company_id = fp.company_id

JOIN fundamentals.balance_sheets b
    ON b.period_id = fp.period_id

WHERE c.symbol = 'TCS'
  AND fp.fiscal_year = 2026
  AND fp.period_type = 'ANNUAL';
""")

with engine.connect() as conn:
    row = conn.execute(query).mappings().first()

print("\n" + "=" * 80)
print("FINSIGHT 360 — TCS FY2026 DCF EQUITY BRIDGE INPUT CHECK")
print("=" * 80)

if row is None:
    raise ValueError("TCS FY2026 balance-sheet record not found.")

for key, value in row.items():
    print(f"{key:30} : {value}")

print("\nInput inspection completed successfully.")
