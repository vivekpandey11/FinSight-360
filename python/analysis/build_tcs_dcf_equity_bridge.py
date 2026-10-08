import pandas as pd
from pathlib import Path

# ============================================================
# VERIFIED FY2026 INPUTS
# ============================================================

CASH = 6417.00
LEASE_LIABILITIES = 11283.00

SHARES_OUTSTANDING_CRORE = (
    3618087518 / 10000000
)

# Conservative bridge:
# Cash added, lease liabilities deducted.
# Other investments / deposits excluded until fully standardized.

NET_CASH_CONSERVATIVE = (
    CASH - LEASE_LIABILITIES
)

# ============================================================
# LOAD DCF
# ============================================================

dcf_path = Path(
    "results/tables/"
    "tcs_dcf_enterprise_value.csv"
)

dcf = pd.read_csv(dcf_path)

# ============================================================
# EV -> EQUITY VALUE -> VALUE PER SHARE
# ============================================================

dcf[
    "cash_inr_crore"
] = CASH

dcf[
    "lease_liabilities_inr_crore"
] = LEASE_LIABILITIES

dcf[
    "net_cash_conservative_inr_crore"
] = NET_CASH_CONSERVATIVE

dcf[
    "equity_value_inr_crore"
] = (
    dcf["enterprise_value"]
    + NET_CASH_CONSERVATIVE
)

dcf[
    "shares_outstanding_crore"
] = SHARES_OUTSTANDING_CRORE

dcf[
    "implied_value_per_share"
] = (
    dcf["equity_value_inr_crore"]
    / SHARES_OUTSTANDING_CRORE
)

# ============================================================
# VALIDATION
# ============================================================

assert (
    dcf["equity_value_inr_crore"] > 0
).all()

assert (
    dcf["implied_value_per_share"] > 0
).all()

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

# ============================================================
# SAVE
# ============================================================

output = Path(
    "results/tables/"
    "tcs_dcf_equity_value_conservative.csv"
)

dcf.round(2).to_csv(
    output,
    index=False
)

# ============================================================
# PRINT
# ============================================================

print(
    "\n" +
    "=" * 115
)

print(
    "FINSIGHT 360 — TCS DCF EQUITY VALUE "
    "(CONSERVATIVE CASH-ONLY BRIDGE)"
)

print(
    "=" * 115
)

print(
    f"\nCash: "
    f"₹{CASH:,.2f} crore"
)

print(
    f"Lease liabilities: "
    f"₹{LEASE_LIABILITIES:,.2f} crore"
)

print(
    f"Conservative net cash adjustment: "
    f"₹{NET_CASH_CONSERVATIVE:,.2f} crore"
)

print(
    f"Shares outstanding: "
    f"{SHARES_OUTSTANDING_CRORE:.4f} crore"
)

print(
    "\nNOTE: Eligible investments and other "
    "liquid financial assets are excluded "
    "from this conservative bridge."
)

print(
    "\n" +
    "-" * 115
)

for _, r in dcf.iterrows():

    print(
        f"{r['scenario']:5s} | "
        f"EV=₹{r['enterprise_value']:,.2f} Cr | "
        f"Equity Value="
        f"₹{r['equity_value_inr_crore']:,.2f} Cr | "
        f"Implied Value/Share="
        f"₹{r['implied_value_per_share']:,.2f}"
    )

print(
    "\n" +
    "-" * 115
)

print(
    f"Bear/Base/Bull implied values: "
    f"₹{bear:,.2f} / "
    f"₹{base:,.2f} / "
    f"₹{bull:,.2f}"
)

print(
    f"\nSaved -> {output}"
)

print(
    "\nConservative DCF equity-value "
    "bridge completed successfully."
)
