from pathlib import Path
import json
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "config" / "universe.json"
RAW_DIR = ROOT / "data" / "raw" / "market"
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results" / "tables"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def main():
    config = load_config()

    assets = {}

    for symbol, info in config["companies"].items():
        assets[symbol] = {
            "name": info["name"],
            "ticker": info["ticker"],
            "asset_type": "company"
        }

    for symbol, info in config["benchmarks"].items():
        assets[symbol] = {
            "name": info["name"],
            "ticker": info["ticker"],
            "asset_type": "benchmark"
        }

    start_date = config["market_data"]["start_date"]

    all_data = []
    quality = []

    print("=" * 70)
    print("FinSight 360 - Market Data Pipeline")
    print("=" * 70)

    for symbol, info in assets.items():

        print(f"\nDownloading {symbol} ({info['ticker']})...")

        try:
            df = yf.download(
                info["ticker"],
                start=start_date,
                auto_adjust=False,
                progress=False
            )

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty:
                print("FAILED - No data returned")

                quality.append({
                    "symbol": symbol,
                    "ticker": info["ticker"],
                    "rows": 0,
                    "start_date": "",
                    "end_date": "",
                    "missing_values": "",
                    "status": "FAIL"
                })

                continue

            raw_file = RAW_DIR / f"{symbol.lower()}_market.csv"
            df.to_csv(raw_file)

            df = df.reset_index()

            df.columns = [
                str(col).lower().replace(" ", "_")
                for col in df.columns
            ]

            df["symbol"] = symbol
            df["company_name"] = info["name"]
            df["ticker"] = info["ticker"]
            df["asset_type"] = info["asset_type"]

            df["date"] = pd.to_datetime(df["date"])

            duplicate_count = int(df.duplicated(subset=["date"]).sum())
            missing_count = int(df.isna().sum().sum())

            invalid_prices = 0

            price_columns = ["open", "high", "low", "close"]

            if all(col in df.columns for col in price_columns):
                invalid_prices = int(
                    (df[price_columns] <= 0).any(axis=1).sum()
                )

            status = (
                "PASS"
                if duplicate_count == 0 and invalid_prices == 0
                else "REVIEW"
            )

            quality.append({
                "symbol": symbol,
                "ticker": info["ticker"],
                "rows": len(df),
                "start_date": df["date"].min().date(),
                "end_date": df["date"].max().date(),
                "missing_values": missing_count,
                "duplicate_dates": duplicate_count,
                "invalid_prices": invalid_prices,
                "status": status
            })

            all_data.append(df)

            print(
                f"OK - {len(df):,} rows | "
                f"{df['date'].min().date()} to "
                f"{df['date'].max().date()} | "
                f"{status}"
            )

        except Exception as e:

            print(f"ERROR - {e}")

            quality.append({
                "symbol": symbol,
                "ticker": info["ticker"],
                "rows": 0,
                "start_date": "",
                "end_date": "",
                "missing_values": "",
                "status": "FAIL",
                "error": str(e)
            })

    if all_data:

        market = pd.concat(all_data, ignore_index=True)

        market = market.sort_values(
            ["symbol", "date"]
        ).reset_index(drop=True)

        output_file = PROCESSED_DIR / "market_prices.csv"
        market.to_csv(output_file, index=False)

        print("\n" + "=" * 70)
        print(f"Total processed rows: {len(market):,}")
        print(f"Saved: {output_file}")

    quality_df = pd.DataFrame(quality)

    quality_file = RESULTS_DIR / "market_data_quality.csv"
    quality_df.to_csv(quality_file, index=False)

    print(f"Quality report: {quality_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
