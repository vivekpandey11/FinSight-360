from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

with open(
    "sql/analysis/004_daily_market_analytics.sql",
    "r",
    encoding="utf-8-sig"
) as f:
    sql = f.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Created analytics.vw_daily_market_analytics")

summary_query = text("""
WITH summary AS (
    SELECT
        symbol,

        MIN(trade_date) AS start_date,
        MAX(trade_date) AS end_date,
        COUNT(*) AS observations,

        MIN(drawdown_pct) AS max_drawdown_pct,

        AVG(
            rolling_60d_volatility_pct
        ) AS avg_60d_volatility_pct

    FROM analytics.vw_daily_market_analytics

    GROUP BY symbol
),

latest AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        cumulative_return_pct,
        rolling_20d_volatility_pct,
        rolling_60d_volatility_pct

    FROM analytics.vw_daily_market_analytics

    ORDER BY symbol, trade_date DESC
)

SELECT
    s.symbol,
    s.start_date,
    s.end_date,
    s.observations,

    l.cumulative_return_pct,

    ROUND(
        s.max_drawdown_pct,
        2
    ) AS max_drawdown_pct,

    ROUND(
        s.avg_60d_volatility_pct,
        2
    ) AS avg_60d_volatility_pct,

    l.rolling_20d_volatility_pct,
    l.rolling_60d_volatility_pct

FROM summary s

JOIN latest l
    ON l.symbol = s.symbol

ORDER BY s.symbol;
""")

with engine.connect() as conn:
    rows = conn.execute(
        summary_query
    ).mappings().all()

print("\n" + "=" * 125)
print("FINSIGHT 360 — MARKET RISK & RETURN SUMMARY")
print("=" * 125)

for r in rows:

    print(
        f"{r['symbol']:10s} | "
        f"{r['start_date']} -> {r['end_date']} | "
        f"N={r['observations']} | "
        f"Cumulative={r['cumulative_return_pct']}% | "
        f"Max DD={r['max_drawdown_pct']}% | "
        f"Avg 60D Vol={r['avg_60d_volatility_pct']}% | "
        f"Latest 20D Vol={r['rolling_20d_volatility_pct']}% | "
        f"Latest 60D Vol={r['rolling_60d_volatility_pct']}%"
    )

print(
    "\nDaily returns, drawdowns and rolling volatility "
    "created successfully."
)
