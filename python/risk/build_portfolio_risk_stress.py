import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from utils.db import get_engine

CAPITAL = 1_000_000
TRADING_DAYS = 252
SYMBOLS = ["TCS", "INFY", "HCLTECH"]

engine = get_engine()

# ============================================================
# LOAD RETURNS
# ============================================================

query = text("""
SELECT
    symbol,
    trade_date,
    daily_return_pct
FROM analytics.vw_daily_market_analytics
WHERE symbol IN ('TCS', 'INFY', 'HCLTECH')
  AND daily_return_pct IS NOT NULL
ORDER BY trade_date, symbol;
""")

with engine.connect() as conn:
    raw = pd.read_sql(query, conn)

returns = raw.pivot(
    index="trade_date",
    columns="symbol",
    values="daily_return_pct"
)

returns = returns[SYMBOLS].dropna()

# DB stores percentage returns -> convert to decimals
returns = returns / 100.0

# ============================================================
# LOAD PORTFOLIO WEIGHTS
# ============================================================

summary = pd.read_csv(
    "results/tables/portfolio_strategy_summary.csv"
)

risk_rows = []
daily_portfolios = {}

# ============================================================
# RISK ENGINE
# ============================================================

for _, p in summary.iterrows():

    name = p["portfolio"]

    weights = np.array([
        p["TCS"],
        p["INFY"],
        p["HCLTECH"]
    ], dtype=float)

    # Daily portfolio return
    port_ret = returns.dot(weights)

    daily_portfolios[name] = port_ret

    # Wealth index
    wealth = (1 + port_ret).cumprod()

    running_peak = wealth.cummax()

    drawdown = (
        wealth / running_peak
    ) - 1

    max_drawdown = drawdown.min()

    worst_day = port_ret.min()

    worst_day_date = port_ret.idxmin()

    # Historical VaR / CVaR 95%
    var_95 = port_ret.quantile(0.05)

    cvar_95 = port_ret[
        port_ret <= var_95
    ].mean()

    negative_returns = port_ret[
        port_ret < 0
    ]

    downside_vol = (
        negative_returns.std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )

    annual_vol = (
        port_ret.std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )

    # Capital impacts
    var_loss_inr = (
        abs(var_95) * CAPITAL
    )

    cvar_loss_inr = (
        abs(cvar_95) * CAPITAL
    )

    max_drawdown_loss_inr = (
        abs(max_drawdown) * CAPITAL
    )

    risk_rows.append({
        "portfolio": name,
        "annual_volatility_pct":
            annual_vol * 100,
        "downside_volatility_pct":
            downside_vol * 100,
        "historical_var_95_daily_pct":
            var_95 * 100,
        "historical_cvar_95_daily_pct":
            cvar_95 * 100,
        "worst_day_pct":
            worst_day * 100,
        "worst_day_date":
            worst_day_date,
        "max_drawdown_pct":
            max_drawdown * 100,
        "var_95_loss_on_10lakh_inr":
            var_loss_inr,
        "cvar_95_loss_on_10lakh_inr":
            cvar_loss_inr,
        "max_drawdown_loss_on_10lakh_inr":
            max_drawdown_loss_inr
    })

risk = pd.DataFrame(risk_rows)

# ============================================================
# SIMPLE SCENARIO STRESS TESTS
# ============================================================

stress_scenarios = {
    "Broad IT Selloff": {
        "TCS": -0.12,
        "INFY": -0.14,
        "HCLTECH": -0.15
    },

    "Severe Tech Shock": {
        "TCS": -0.20,
        "INFY": -0.22,
        "HCLTECH": -0.25
    },

    "TCS Specific Shock": {
        "TCS": -0.18,
        "INFY": -0.05,
        "HCLTECH": -0.05
    },

    "HCLTECH Specific Shock": {
        "TCS": -0.05,
        "INFY": -0.05,
        "HCLTECH": -0.20
    }
}

stress_rows = []

for _, p in summary.iterrows():

    name = p["portfolio"]

    weights = {
        symbol: float(p[symbol])
        for symbol in SYMBOLS
    }

    for scenario, shocks in stress_scenarios.items():

        portfolio_shock = sum(
            weights[symbol]
            * shocks[symbol]
            for symbol in SYMBOLS
        )

        stress_rows.append({
            "portfolio":
                name,

            "scenario":
                scenario,

            "portfolio_loss_pct":
                portfolio_shock * 100,

            "loss_on_10lakh_inr":
                abs(
                    portfolio_shock
                    * CAPITAL
                ),

            "post_stress_value_inr":
                CAPITAL * (
                    1 + portfolio_shock
                )
        })

stress = pd.DataFrame(
    stress_rows
)

# ============================================================
# VALIDATION
# ============================================================

assert len(risk) == 3
assert len(stress) == 12

assert (
    risk[
        "historical_cvar_95_daily_pct"
    ]
    <=
    risk[
        "historical_var_95_daily_pct"
    ]
).all()

assert (
    risk["max_drawdown_pct"] < 0
).all()

assert (
    stress["portfolio_loss_pct"] < 0
).all()

# ============================================================
# SAVE
# ============================================================

output_dir = Path(
    "results/tables"
)

risk_path = (
    output_dir /
    "portfolio_risk_metrics.csv"
)

stress_path = (
    output_dir /
    "portfolio_stress_tests.csv"
)

risk.round(4).to_csv(
    risk_path,
    index=False
)

stress.round(2).to_csv(
    stress_path,
    index=False
)

# ============================================================
# PRINT
# ============================================================

print("\n" + "=" * 118)

print(
    "FINSIGHT 360 — PORTFOLIO RISK "
    "AND STRESS TESTING"
)

print("=" * 118)

for _, r in risk.iterrows():

    print("\n" + "-" * 118)

    print(r["portfolio"].upper())

    print(
        f"Annual volatility      : "
        f"{r['annual_volatility_pct']:.2f}%"
    )

    print(
        f"Downside volatility    : "
        f"{r['downside_volatility_pct']:.2f}%"
    )

    print(
        f"Historical VaR 95%     : "
        f"{r['historical_var_95_daily_pct']:.2f}% "
        f"(₹{r['var_95_loss_on_10lakh_inr']:,.0f})"
    )

    print(
        f"Historical CVaR 95%    : "
        f"{r['historical_cvar_95_daily_pct']:.2f}% "
        f"(₹{r['cvar_95_loss_on_10lakh_inr']:,.0f})"
    )

    print(
        f"Worst single day       : "
        f"{r['worst_day_pct']:.2f}% "
        f"on {r['worst_day_date']}"
    )

    print(
        f"Maximum drawdown       : "
        f"{r['max_drawdown_pct']:.2f}% "
        f"(₹{r['max_drawdown_loss_on_10lakh_inr']:,.0f})"
    )

print("\n" + "=" * 118)

print("SCENARIO STRESS TESTS — ₹10 LAKH")

print("=" * 118)

for portfolio in summary["portfolio"]:

    print(f"\n{portfolio}")

    subset = stress[
        stress["portfolio"] == portfolio
    ]

    for _, r in subset.iterrows():

        print(
            f"  {r['scenario']:24s} | "
            f"{r['portfolio_loss_pct']:7.2f}% | "
            f"Loss ₹{r['loss_on_10lakh_inr']:,.0f} | "
            f"Remaining ₹{r['post_stress_value_inr']:,.0f}"
        )

print(f"\nSaved -> {risk_path}")
print(f"Saved -> {stress_path}")

print(
    "\nNOTE: Scenario shocks are analytical "
    "stress assumptions, not forecasts."
)

print(
    "\nPortfolio risk and stress-testing "
    "completed successfully."
)
