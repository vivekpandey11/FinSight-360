from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

dependency_sql = text("""
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
  AND source_view.relname = 'vw_dupont_analysis'
  AND dependent_view.oid <> source_view.oid
ORDER BY 1, 2;
""")

with engine.connect() as conn:
    dependencies = conn.execute(dependency_sql).mappings().all()

print("=== DUPONT VIEW DEPENDENCIES ===")

if dependencies:
    for row in dependencies:
        print(dict(row))

    raise SystemExit(
        "STOP: Dependent objects exist. View was NOT dropped."
    )

print("NONE")
print("Safe to recreate view.")

with open(
    "sql/analysis/003_dupont_analysis.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    create_sql = f.read()

with engine.begin() as conn:
    conn.execute(
        text("DROP VIEW IF EXISTS analytics.vw_dupont_analysis")
    )
    conn.execute(text(create_sql))

print("✓ analytics.vw_dupont_analysis recreated successfully.")
