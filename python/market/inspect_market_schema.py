from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

query = text("""
SELECT
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'market'
  AND table_name = 'market_prices'
ORDER BY ordinal_position;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\nMARKET.MARKET_PRICES SCHEMA")
print("=" * 70)

for r in rows:
    print(
        f"{r['ordinal_position']:2} | "
        f"{r['column_name']:25} | "
        f"{r['data_type']}"
    )
