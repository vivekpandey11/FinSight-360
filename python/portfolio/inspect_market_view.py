from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

query = text("""
SELECT
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'analytics'
  AND table_name = 'vw_daily_market_analytics'
ORDER BY ordinal_position;
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print("\nanalytics.vw_daily_market_analytics")
print("=" * 70)

for r in rows:
    print(
        f"{r['ordinal_position']:2} | "
        f"{r['column_name']:35} | "
        f"{r['data_type']}"
    )

print("\nTotal columns:", len(rows))
