import pandas as pd
from pathlib import Path
from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

query = text("""
WITH latest_price AS (
    SELECT DISTINCT ON (c.symbol)
        c.company_id,
        c.symbol,
        mp.trade_date,
        mp.close_price
    FROM core.companies c
    JOIN market.market_prices mp
        ON mp.company_id = c.company_id
    WHERE c.symbol IN ('TCS', 'INFY', 'HCLTECH')
    ORDER BY c.symbol, mp.trade_date DESC
)
SELECT
    c.symbol,
    fp.fiscal_year,
    lp.trade_date,
    lp.close_price,
    i.revenue,
    i.ebitda,
    i.ebit,
    i.net_income,
    i.eps,
    cf.free_cash_flow
FROM core.companies c
JOIN fundamentals.financial_periods fp
    ON fp.company_id = c.company_id
JOIN fundamentals.income_statements i
    ON i.period_id = fp.period_id
JOIN fundamentals.cash_flows cf
    ON cf.period_id = fp.period_id
JOIN latest_price lp
    ON lp.company_id = c.company_id
WHERE
    c.symbol IN ('TCS', 'INFY', 'HCLTECH')
    AND fp.period_type = 'ANNUAL'
    AND fp.fiscal_year = 2026
ORDER BY c.symbol;
""")

with engine.connect() as conn:
    df = pd.read_sql(query, conn)

# ------------------------------------------------------------
# VALUATION + QUALITY METRICS
# ------------------------------------------------------------

df["pe_ratio"] = (
    df["close_price"] / df["eps"]
)

df["earnings_yield_pct"] = (
    df["eps"] / df["close_price"]
) * 100

df["ebitda_margin_pct"] = (
    df["ebitda"] / df["revenue"]
) * 100

df["ebit_margin_pct"] = (
    df["ebit"] / df["revenue"]
) * 100

df["net_margin_pct"] = (
    df["net_income"] / df["revenue"]
) * 100

df["fcf_margin_pct"] = (
    df["free_cash_flow"] / df["revenue"]
) * 100

df["fcf_to_pat_pct"] = (
    df["free_cash_flow"] / df["net_income"]
) * 100

# ------------------------------------------------------------
# PEER P/E BENCHMARK
# TCS excluded from peer median used to value TCS
# ------------------------------------------------------------

peers = df[
    df["symbol"].isin(["INFY", "HCLTECH"])
].copy()

peer_median_pe = peers["pe_ratio"].median()
peer_mean_pe = peers["pe_ratio"].mean()

tcs = df[
    df["symbol"] == "TCS"
].iloc[0]

tcs_eps = float(tcs["eps"])
tcs_price = float(tcs["close_price"])

tcs_value_peer_median = (
    tcs_eps * peer_median_pe
)

tcs_value_peer_mean = (
    tcs_eps * peer_mean_pe
)

tcs_peer_upside_pct = (
    (tcs_value_peer_median / tcs_price) - 1
) * 100

# ------------------------------------------------------------
# RANKING
# Lower P/E is cheaper.
# Higher margins / FCF conversion are stronger.
# ------------------------------------------------------------

df["pe_rank"] = (
    df["pe_ratio"]
    .rank(method="min", ascending=True)
)

df["ebitda_margin_rank"] = (
    df["ebitda_margin_pct"]
    .rank(method="min", ascending=False)
)

df["fcf_conversion_rank"] = (
    df["fcf_to_pat_pct"]
    .rank(method="min", ascending=False)
)

# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

assert len(df) == 3
assert (df["pe_ratio"] > 0).all()
assert (df["earnings_yield_pct"] > 0).all()
assert peer_median_pe > 0
assert tcs_value_peer_median > 0

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

output_dir = Path("results/tables")
output_dir.mkdir(parents=True, exist_ok=True)

peer_path = (
    output_dir /
    "fy2026_peer_relative_valuation.csv"
)

tcs_path = (
    output_dir /
    "tcs_relative_valuation_summary.csv"
)

df.round(2).to_csv(
    peer_path,
    index=False
)

summary = pd.DataFrame([{
    "valuation_date": tcs["trade_date"],
    "tcs_market_price": tcs_price,
    "tcs_eps_fy2026": tcs_eps,
    "tcs_pe": tcs["pe_ratio"],
    "infy_pe": df.loc[
        df["symbol"] == "INFY",
        "pe_ratio"
    ].iloc[0],
    "hcltech_pe": df.loc[
        df["symbol"] == "HCLTECH",
        "pe_ratio"
    ].iloc[0],
    "peer_median_pe": peer_median_pe,
    "peer_mean_pe": peer_mean_pe,
    "tcs_implied_value_peer_median_pe":
        tcs_value_peer_median,
    "tcs_implied_value_peer_mean_pe":
        tcs_value_peer_mean,
    "tcs_peer_median_upside_downside_pct":
        tcs_peer_upside_pct
}])

summary.round(2).to_csv(
    tcs_path,
    index=False
)

# ------------------------------------------------------------
# PRINT
# ------------------------------------------------------------

print("\n" + "=" * 120)

print(
    "FINSIGHT 360 — FY2026 RELATIVE VALUATION "
    "AND PEER QUALITY"
)

print("=" * 120)

for _, r in df.iterrows():

    print(
        f"\n{r['symbol']}"
        f"\n  Price            : ₹{r['close_price']:,.2f}"
        f"\n  FY2026 EPS       : ₹{r['eps']:,.2f}"
        f"\n  P/E              : {r['pe_ratio']:.2f}x"
        f"\n  Earnings Yield   : {r['earnings_yield_pct']:.2f}%"
        f"\n  EBITDA Margin    : {r['ebitda_margin_pct']:.2f}%"
        f"\n  EBIT Margin      : {r['ebit_margin_pct']:.2f}%"
        f"\n  Net Margin       : {r['net_margin_pct']:.2f}%"
        f"\n  FCF Margin       : {r['fcf_margin_pct']:.2f}%"
        f"\n  FCF / PAT        : {r['fcf_to_pat_pct']:.2f}%"
    )

print("\n" + "-" * 120)

print("TCS RELATIVE VALUATION")

print(
    f"\nTCS current P/E              : "
    f"{tcs['pe_ratio']:.2f}x"
)

print(
    f"INFY + HCLTECH median P/E    : "
    f"{peer_median_pe:.2f}x"
)

print(
    f"INFY + HCLTECH mean P/E      : "
    f"{peer_mean_pe:.2f}x"
)

print(
    f"\nTCS implied value @ median P/E: "
    f"₹{tcs_value_peer_median:,.2f}"
)

print(
    f"TCS implied value @ mean P/E  : "
    f"₹{tcs_value_peer_mean:,.2f}"
)

print(
    f"Relative upside/(downside)     : "
    f"{tcs_peer_upside_pct:+.2f}%"
)

print("\n" + "-" * 120)

print(
    "NOTE: Relative valuation currently uses P/E because "
    "peer net-debt/share-count inputs have not yet been "
    "fully standardized. EV/EBITDA will not be fabricated."
)

print(
    f"\nSaved -> {peer_path}"
)

print(
    f"Saved -> {tcs_path}"
)

print(
    "\nRelative valuation completed successfully."
)
