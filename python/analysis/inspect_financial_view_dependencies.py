from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

sql = text("""
SELECT DISTINCT
    dependent_ns.nspname AS dependent_schema,
    dependent_view.relname AS dependent_view
FROM pg_depend d
JOIN pg_rewrite r
    ON d.objid = r.oid
JOIN pg_class dependent_view
    ON r.ev_class = dependent_view.oid
JOIN pg_namespace dependent_ns
    ON dependent_view.relnamespace = dependent_ns.oid
JOIN pg_class source_view
    ON d.refobjid = source_view.oid
JOIN pg_namespace source_ns
    ON source_view.relnamespace = source_ns.oid
WHERE source_ns.nspname = 'analytics'
  AND source_view.relname = 'vw_financial_performance'
  AND dependent_view.oid <> source_view.oid
ORDER BY 1, 2;
""")

with engine.connect() as conn:
    rows = conn.execute(sql).mappings().all()

print("=== FINANCIAL PERFORMANCE DEPENDENCIES ===")

if not rows:
    print("NONE")
else:
    for row in rows:
        print(dict(row))
