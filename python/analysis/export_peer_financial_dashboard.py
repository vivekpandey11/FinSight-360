from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

out = Path("powerbi/data/peer_financial_performance.csv")
out.parent.mkdir(parents=True, exist_ok=True)

engine = get_engine()

with engine.connect() as conn:
    df = pd.read_sql(
        text("""
            SELECT *
            FROM analytics.vw_financial_performance
            ORDER BY symbol, fiscal_year
        """),
        conn
    )

if len(df) != 15:
    raise RuntimeError(
        f"Expected 15 company-years, found {len(df)}"
    )

if df["symbol"].nunique() != 3:
    raise RuntimeError("Expected three companies")

df.to_csv(out, index=False)

print("=== PEER FINANCIAL DASHBOARD ===")
print("Rows:", len(df))
print("Companies:", df["symbol"].unique().tolist())
print("Columns:", df.columns.tolist())
print("Saved:", out)
print("PASS")
