import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from utils.db import get_engine

# ============================================================
# CONFIG
# ============================================================

CAPITAL = 1_000_000
TRADING_DAYS = 252
RISK_FREE_RATE = 0.0

SYMBOLS = [
    "TCS",
    "INFY",
    "HCLTECH"
]

engine = get_engine()

# ============================================================
# LOAD DAILY RETURNS
# ============================================================

query = text("""
SELECT
    symbol,
    trade_date,
    daily_return_pct
FROM analytics.vw_daily_market_analytics
WHERE
    symbol IN ('TCS', 'INFY', 'HCLTECH')
    AND daily_return_pct IS NOT NULL
ORDER BY trade_date, symbol;
""")

with engine.connect() as conn:
    raw = pd.read_sql(
        query,
        conn
    )

returns = raw.pivot(
    index="trade_date",
    columns="symbol",
    values="daily_return_pct"
)

returns = returns[
    SYMBOLS
].dropna()

# Detect whether DB returns are decimals or percentages
if returns.abs().median().median() > 0.20:
    returns = returns / 100.0

# ============================================================
# EXPECTED RETURN + COVARIANCE
# ============================================================

mean_daily = returns.mean()

annual_returns = (
    (1 + mean_daily) ** TRADING_DAYS
) - 1

cov_matrix = (
    returns.cov()
    * TRADING_DAYS
)

# ============================================================
# PORTFOLIO CALCULATION
# ============================================================

def portfolio_metrics(weights):

    weights = np.array(weights)

    expected_return = np.dot(
        weights,
        annual_returns.values
    )

    variance = np.dot(
        weights.T,
        np.dot(
            cov_matrix.values,
            weights
        )
    )

    volatility = np.sqrt(
        variance
    )

    sharpe = (
        (expected_return - RISK_FREE_RATE)
        / volatility
        if volatility > 0
        else np.nan
    )

    return (
        expected_return,
        volatility,
        sharpe
    )

# ============================================================
# MONTE CARLO PORTFOLIOS
# ============================================================

np.random.seed(42)

n_portfolios = 100_000

records = []

for _ in range(n_portfolios):

    weights = np.random.random(
        len(SYMBOLS)
    )

    weights /= weights.sum()

    ret, vol, sharpe = (
        portfolio_metrics(weights)
    )

    records.append(
        [
            *weights,
            ret,
            vol,
            sharpe
        ]
    )

columns = (
    SYMBOLS
    + [
        "expected_return",
        "volatility",
        "sharpe_ratio"
    ]
)

sim = pd.DataFrame(
    records,
    columns=columns
)

# ============================================================
# SELECT PORTFOLIOS
# ============================================================

equal_weights = np.array(
    [1 / len(SYMBOLS)] * len(SYMBOLS)
)

eq_ret, eq_vol, eq_sharpe = (
    portfolio_metrics(
        equal_weights
    )
)

min_vol_row = sim.loc[
    sim["volatility"].idxmin()
]

max_sharpe_row = sim.loc[
    sim["sharpe_ratio"].idxmax()
]

portfolio_rows = []

portfolio_rows.append({
    "portfolio":
        "Equal Weight",

    **{
        symbol:
            equal_weights[i]
        for i, symbol
        in enumerate(SYMBOLS)
    },

    "expected_return":
        eq_ret,

    "volatility":
        eq_vol,

    "sharpe_ratio":
        eq_sharpe
})

for name, row in [
    (
        "Minimum Volatility",
        min_vol_row
    ),
    (
        "Maximum Sharpe",
        max_sharpe_row
    )
]:

    portfolio_rows.append({
        "portfolio":
            name,

        **{
            symbol:
                row[symbol]
            for symbol
            in SYMBOLS
        },

        "expected_return":
            row["expected_return"],

        "volatility":
            row["volatility"],

        "sharpe_ratio":
            row["sharpe_ratio"]
    })

summary = pd.DataFrame(
    portfolio_rows
)

# ============================================================
# CAPITAL ALLOCATION
# ============================================================

allocation_rows = []

for _, row in summary.iterrows():

    for symbol in SYMBOLS:

        allocation_rows.append({
            "portfolio":
                row["portfolio"],

            "symbol":
                symbol,

            "weight_pct":
                row[symbol] * 100,

            "allocation_inr":
                CAPITAL * row[symbol]
        })

allocation = pd.DataFrame(
    allocation_rows
)

# ============================================================
# VALIDATION
# ============================================================

assert len(returns) > 1000

for _, row in summary.iterrows():

    total_weight = sum(
        row[s]
        for s in SYMBOLS
    )

    assert abs(
        total_weight - 1
    ) < 1e-6

assert (
    summary["volatility"] > 0
).all()

# ============================================================
# SAVE
# ============================================================

output_dir = Path(
    "results/tables"
)

summary_path = (
    output_dir /
    "portfolio_strategy_summary.csv"
)

allocation_path = (
    output_dir /
    "portfolio_10lakh_allocation.csv"
)

correlation_path = (
    output_dir /
    "portfolio_asset_correlation.csv"
)

summary.round(6).to_csv(
    summary_path,
    index=False
)

allocation.round(2).to_csv(
    allocation_path,
    index=False
)

returns.corr().round(4).to_csv(
    correlation_path
)

# ============================================================
# PRINT
# ============================================================

print(
    "\n" +
    "=" * 115
)

print(
    "FINSIGHT 360 — ₹10 LAKH "
    "PORTFOLIO CONSTRUCTION"
)

print(
    "=" * 115
)

print(
    f"\nCommon observations: "
    f"{len(returns):,}"
)

print(
    f"Period: "
    f"{returns.index.min()} "
    f"to {returns.index.max()}"
)

print(
    "\nNOTE: Sharpe ratio currently uses "
    "0% risk-free rate for consistency "
    "with existing market-risk module."
)

for _, r in summary.iterrows():

    print(
        "\n" +
        "-" * 115
    )

    print(
        r["portfolio"].upper()
    )

    print(
        f"TCS weight      : "
        f"{r['TCS'] * 100:.2f}%"
    )

    print(
        f"INFY weight     : "
        f"{r['INFY'] * 100:.2f}%"
    )

    print(
        f"HCLTECH weight  : "
        f"{r['HCLTECH'] * 100:.2f}%"
    )

    print(
        f"Expected return : "
        f"{r['expected_return'] * 100:.2f}%"
    )

    print(
        f"Volatility      : "
        f"{r['volatility'] * 100:.2f}%"
    )

    print(
        f"Sharpe ratio    : "
        f"{r['sharpe_ratio']:.4f}"
    )

print(
    "\n" +
    "=" * 115
)

print(
    "₹10 LAKH CAPITAL ALLOCATION"
)

print(
    "=" * 115
)

for portfolio in summary[
    "portfolio"
]:

    print(
        f"\n{portfolio}:"
    )

    subset = allocation[
        allocation["portfolio"]
        == portfolio
    ]

    for _, r in subset.iterrows():

        print(
            f"  {r['symbol']:8s} "
            f"{r['weight_pct']:6.2f}%  "
            f"₹{r['allocation_inr']:,.0f}"
        )

print(
    f"\nSaved -> {summary_path}"
)

print(
    f"Saved -> {allocation_path}"
)

print(
    f"Saved -> {correlation_path}"
)

print(
    "\nPortfolio construction "
    "completed successfully."
)

