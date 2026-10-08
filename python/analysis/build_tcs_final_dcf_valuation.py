import pandas as pd
from pathlib import Path
from sqlalchemy import text
from utils.db import get_engine

# ============================================================
# TCS FY2026 VERIFIED / SOURCE-BACKED BRIDGE
# INR CRORE
# ============================================================

CASH = 6417.00

TOTAL_BANK_DEPOSITS = 7216.00
RESTRICTED_ST_BANK_DEPOSITS = 2289.00
RESTRICTED_LT_BANK_DEPOSITS = 730.00

TOTAL_INVESTMENTS = 33770.00
RESTRICTED_NONCURRENT_INVESTMENTS = 218.00
RESTRICTED_CURRENT_INVESTMENTS = 279.00

LEASE_LIABILITIES = 11283.00

# Total equity 108,478 - parent shareholders' equity 107,240
NCI = 1238.00

CLASS_B_PREFERENCE_LIABILITY = 126.00

SHARES_OUTSTANDING_CRORE = (
    3618087518 / 10_000_000
)

# ============================================================
# CALCULATE ELIGIBLE FINANCIAL ASSETS
# ============================================================

UNRESTRICTED_BANK_DEPOSITS = (
    TOTAL_BANK_DEPOSITS
    - RESTRICTED_ST_BANK_DEPOSITS
    - RESTRICTED_LT_BANK_DEPOSITS
)

UNRESTRICTED_INVESTMENTS = (
    TOTAL_INVESTMENTS
    - RESTRICTED_NONCURRENT_INVESTMENTS
    - RESTRICTED_CURRENT_INVESTMENTS
)

ADJUSTED_NET_FINANCIAL_ASSETS = (
    CASH
    + UNRESTRICTED_BANK_DEPOSITS
    + UNRESTRICTED_INVESTMENTS
    - LEASE_LIABILITIES
    - NCI
    - CLASS_B_PREFERENCE_LIABILITY
)

# ============================================================
# LOAD DCF ENTERPRISE VALUES
# ============================================================

dcf_path = Path(
    "results/tables/tcs_dcf_enterprise_value.csv"
)

dcf = pd.read_csv(dcf_path)

dcf[
    "adjusted_net_financial_assets"
] = ADJUSTED_NET_FINANCIAL_ASSETS

dcf[
    "parent_equity_value"
] = (
    dcf["enterprise_value"]
    + ADJUSTED_NET_FINANCIAL_ASSETS
)

dcf[
    "shares_outstanding_crore"
] = SHARES_OUTSTANDING_CRORE

dcf[
    "implied_value_per_share"
] = (
    dcf["parent_equity_value"]
    / SHARES_OUTSTANDING_CRORE
)

# ============================================================
# LATEST MARKET PRICE FROM DATABASE
# IMPORTANT: use close_price, NOT adjusted_close
# ============================================================

engine = get_engine()

query = text("""
SELECT
    mp.trade_date,
    mp.close_price
FROM market.market_prices mp
JOIN core.companies c
    ON c.company_id = mp.company_id
WHERE c.symbol = 'TCS'
ORDER BY mp.trade_date DESC
LIMIT 1;
""")

with engine.connect() as conn:
    market = conn.execute(
        query
    ).mappings().first()

if market is None:
    raise ValueError(
        "Latest TCS market price not found."
    )

latest_date = market["trade_date"]
latest_price = float(
    market["close_price"]
)

dcf[
    "reference_market_price"
] = latest_price

dcf[
    "upside_downside_pct"
] = (
    (
        dcf["implied_value_per_share"]
        / latest_price
    ) - 1
) * 100

# ============================================================
# PER-SHARE WACC x TERMINAL-GROWTH SENSITIVITY
# ============================================================

sensitivity_path = Path(
    "results/tables/"
    "tcs_dcf_sensitivity_long.csv"
)

sens = pd.read_csv(
    sensitivity_path
)

sens[
    "parent_equity_value"
] = (
    sens["enterprise_value_inr_crore"]
    + ADJUSTED_NET_FINANCIAL_ASSETS
)

sens[
    "implied_value_per_share"
] = (
    sens["parent_equity_value"]
    / SHARES_OUTSTANDING_CRORE
)

matrix = sens.pivot(
    index="wacc_pct",
    columns="terminal_growth_pct",
    values="implied_value_per_share"
)

matrix.index.name = "WACC %"

matrix.columns = [
    f"g={x:.1f}%"
    for x in matrix.columns
]

# ============================================================
# VALIDATIONS
# ============================================================

assert UNRESTRICTED_BANK_DEPOSITS == 4197
assert UNRESTRICTED_INVESTMENTS == 33273
assert ADJUSTED_NET_FINANCIAL_ASSETS == 31240

bear = dcf.loc[
    dcf["scenario"] == "Bear",
    "implied_value_per_share"
].iloc[0]

base = dcf.loc[
    dcf["scenario"] == "Base",
    "implied_value_per_share"
].iloc[0]

bull = dcf.loc[
    dcf["scenario"] == "Bull",
    "implied_value_per_share"
].iloc[0]

assert bear < base < bull

assert latest_price > 0

# ============================================================
# SAVE
# ============================================================

output_dir = Path(
    "results/tables"
)

bridge_path = (
    output_dir /
    "tcs_dcf_final_equity_valuation.csv"
)

sensitivity_output = (
    output_dir /
    "tcs_dcf_per_share_sensitivity.csv"
)

dcf.round(2).to_csv(
    bridge_path,
    index=False
)

matrix.round(2).to_csv(
    sensitivity_output
)

# ============================================================
# PRINT
# ============================================================

print("\n" + "=" * 115)

print(
    "FINSIGHT 360 — TCS FINAL ADJUSTED DCF "
    "EQUITY VALUATION"
)

print("=" * 115)

print("\nFY2026 EV -> PARENT EQUITY BRIDGE")

print(
    f"Cash & equivalents                  "
    f"₹{CASH:,.2f} Cr"
)

print(
    f"Unrestricted bank deposits          "
    f"₹{UNRESTRICTED_BANK_DEPOSITS:,.2f} Cr"
)

print(
    f"Unrestricted investments            "
    f"₹{UNRESTRICTED_INVESTMENTS:,.2f} Cr"
)

print(
    f"Less: Lease liabilities             "
    f"₹{LEASE_LIABILITIES:,.2f} Cr"
)

print(
    f"Less: Non-controlling interests     "
    f"₹{NCI:,.2f} Cr"
)

print(
    f"Less: Class-B preference liability  "
    f"₹{CLASS_B_PREFERENCE_LIABILITY:,.2f} Cr"
)

print("-" * 75)

print(
    f"Adjusted net financial assets       "
    f"₹{ADJUSTED_NET_FINANCIAL_ASSETS:,.2f} Cr"
)

print(
    f"\nShares outstanding                  "
    f"{SHARES_OUTSTANDING_CRORE:.4f} Cr"
)

print(
    f"Latest available TCS close          "
    f"₹{latest_price:,.2f}"
)

print(
    f"Market-price date                   "
    f"{latest_date}"
)

print("\n" + "-" * 115)

for _, r in dcf.iterrows():

    print(
        f"{r['scenario']:5s} | "
        f"EV=₹{r['enterprise_value']:,.2f} Cr | "
        f"Parent Equity="
        f"₹{r['parent_equity_value']:,.2f} Cr | "
        f"Value/Share="
        f"₹{r['implied_value_per_share']:,.2f} | "
        f"Upside/(Downside)="
        f"{r['upside_downside_pct']:+.2f}%"
    )

print("\n" + "=" * 115)

print(
    "BASE-CASE PER-SHARE SENSITIVITY"
)

print("=" * 115)

print(
    matrix.round(0).to_string()
)

print("\nVALIDATION PASSED:")

print(
    "✓ Restricted-purpose financial assets excluded"
)

print(
    "✓ Lease liabilities deducted"
)

print(
    "✓ NCI deducted for parent-equity bridge"
)

print(
    "✓ Preference-share liability deducted"
)

print(
    "✓ Bear < Base < Bull"
)

print(
    "✓ Market comparison uses actual close_price"
)

print(
    f"\nSaved -> {bridge_path}"
)

print(
    f"Saved -> {sensitivity_output}"
)

print(
    "\nNOTE: DCF is anchored to FY2026 year-end. "
    "Latest market close is shown only as a "
    "reference comparison."
)

print(
    "\nFinal adjusted DCF valuation completed successfully."
)
