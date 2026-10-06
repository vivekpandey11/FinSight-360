from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from python.utils.db import get_engine

FILE = ROOT / "data" / "processed" / "market_prices.csv"


def main():
    df = pd.read_csv(FILE)

    print("=" * 60)
    print("FinSight 360 - PostgreSQL Market Loader")
    print("=" * 60)
    print(f"Source rows: {len(df):,}")

    engine = get_engine()

    with engine.begin() as conn:

        # 1. Load company / benchmark master
        assets = (
            df[
                ["symbol", "company_name", "ticker", "asset_type"]
            ]
            .drop_duplicates()
        )

        company_sql = text("""
            INSERT INTO core.companies
                (symbol, company_name, ticker, asset_type,
                 sector, industry, currency)
            VALUES
                (:symbol, :company_name, :ticker, :asset_type,
                 :sector, :industry, 'INR')
            ON CONFLICT (symbol)
            DO UPDATE SET
                company_name = EXCLUDED.company_name,
                ticker = EXCLUDED.ticker;
        """)

        for row in assets.to_dict("records"):
            is_company = row["asset_type"] == "company"

            conn.execute(
                company_sql,
                {
                    **row,
                    "sector": (
                        "Information Technology"
                        if is_company else "Benchmark"
                    ),
                    "industry": (
                        "IT Services"
                        if is_company else "Market Index"
                    )
                }
            )

        print(f"Assets loaded: {len(assets)}")

        # 2. Get database IDs
        mapping = dict(
            conn.execute(
                text("""
                    SELECT symbol, company_id
                    FROM core.companies
                """)
            ).fetchall()
        )

        # 3. Prepare market data
        df["company_id"] = df["symbol"].map(mapping)
        df["trade_date"] = pd.to_datetime(df["date"]).dt.date

        adj_col = (
            "adj_close"
            if "adj_close" in df.columns
            else "adjusted_close"
        )

        records = []

        for row in df.to_dict("records"):
            records.append({
                "company_id": int(row["company_id"]),
                "trade_date": row["trade_date"],
                "open_price": row["open"],
                "high_price": row["high"],
                "low_price": row["low"],
                "close_price": row["close"],
                "adjusted_close": row.get(adj_col),
                "volume": int(row["volume"])
            })

        # 4. Insert / update market prices
        market_sql = text("""
            INSERT INTO market.market_prices
                (
                    company_id,
                    trade_date,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    adjusted_close,
                    volume
                )
            VALUES
                (
                    :company_id,
                    :trade_date,
                    :open_price,
                    :high_price,
                    :low_price,
                    :close_price,
                    :adjusted_close,
                    :volume
                )
            ON CONFLICT (company_id, trade_date)
            DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                adjusted_close = EXCLUDED.adjusted_close,
                volume = EXCLUDED.volume;
        """)

        batch_size = 1000

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            conn.execute(market_sql, batch)

            print(
                f"Loaded {min(i + batch_size, len(records)):,}"
                f"/{len(records):,}"
            )

        # 5. Validation
        asset_count = conn.execute(
            text("SELECT COUNT(*) FROM core.companies")
        ).scalar_one()

        market_count = conn.execute(
            text("SELECT COUNT(*) FROM market.market_prices")
        ).scalar_one()

        duplicate_count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT company_id, trade_date
                    FROM market.market_prices
                    GROUP BY company_id, trade_date
                    HAVING COUNT(*) > 1
                ) x
            """)
        ).scalar_one()

        null_close = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM market.market_prices
                WHERE close_price IS NULL
            """)
        ).scalar_one()

        print("\nDATABASE VALIDATION")
        print("-" * 40)
        print(f"Assets             : {asset_count}")
        print(f"Market rows        : {market_count:,}")
        print(f"Duplicate rows     : {duplicate_count}")
        print(f"NULL close prices  : {null_close}")

    print("\nTransaction committed successfully.")


if __name__ == "__main__":
    main()