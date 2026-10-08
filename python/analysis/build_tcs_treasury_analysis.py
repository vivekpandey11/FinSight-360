import pandas as pd
from pathlib import Path

# ============================================================
# VERIFIED FY2026 TCS LIQUIDITY INPUTS
# INR CRORE
# ============================================================

CASH = 6417.0

TOTAL_BANK_DEPOSITS = 7216.0
RESTRICTED_ST_DEPOSITS = 2289.0
RESTRICTED_LT_DEPOSITS = 730.0

TOTAL_INVESTMENTS = 33770.0
RESTRICTED_NONCURRENT_INVESTMENTS = 218.0
RESTRICTED_CURRENT_INVESTMENTS = 279.0

CURRENT_ASSETS = 135705.0
CURRENT_LIABILITIES = 60914.0

CFO = 52094.0
FCF = 48057.0
DIVIDENDS_PAID = 39437.0

LEASE_LIABILITIES = 11283.0
PREFERENCE_LIABILITY = 126.0

# ============================================================
# LIQUIDITY CALCULATIONS
# ============================================================

unrestricted_deposits = (
    TOTAL_BANK_DEPOSITS
    - RESTRICTED_ST_DEPOSITS
    - RESTRICTED_LT_DEPOSITS
)

unrestricted_investments = (
    TOTAL_INVESTMENTS
    - RESTRICTED_NONCURRENT_INVESTMENTS
    - RESTRICTED_CURRENT_INVESTMENTS
)

core_liquidity = (
    CASH
    + unrestricted_deposits
    + unrestricted_investments
)

debt_like_obligations = (
    LEASE_LIABILITIES
    + PREFERENCE_LIABILITY
)

net_liquidity = (
    core_liquidity
    - debt_like_obligations
)

current_ratio = (
    CURRENT_ASSETS
    / CURRENT_LIABILITIES
)

cash_ratio = (
    CASH
    / CURRENT_LIABILITIES
)

liquid_asset_coverage = (
    core_liquidity
    / CURRENT_LIABILITIES
)

cfo_current_liability_coverage = (
    CFO
    / CURRENT_LIABILITIES
)

dividend_coverage_cfo = (
    CFO
    / DIVIDENDS_PAID
)

dividend_coverage_fcf = (
    FCF
    / DIVIDENDS_PAID
)

dividend_payout_of_fcf = (
    DIVIDENDS_PAID
    / FCF
)

# ============================================================
# KPI TABLE
# ============================================================

kpis = pd.DataFrame([
    {
        "metric": "Cash & Equivalents",
        "value": CASH,
        "unit": "INR Crore"
    },
    {
        "metric": "Unrestricted Bank Deposits",
        "value": unrestricted_deposits,
        "unit": "INR Crore"
    },
    {
        "metric": "Unrestricted Investments",
        "value": unrestricted_investments,
        "unit": "INR Crore"
    },
    {
        "metric": "Core Liquidity Pool",
        "value": core_liquidity,
        "unit": "INR Crore"
    },
    {
        "metric": "Debt-like Obligations",
        "value": debt_like_obligations,
        "unit": "INR Crore"
    },
    {
        "metric": "Net Liquidity",
        "value": net_liquidity,
        "unit": "INR Crore"
    },
    {
        "metric": "Current Ratio",
        "value": current_ratio,
        "unit": "x"
    },
    {
        "metric": "Cash Ratio",
        "value": cash_ratio,
        "unit": "x"
    },
    {
        "metric": "Liquid Asset Coverage",
        "value": liquid_asset_coverage,
        "unit": "x"
    },
    {
        "metric": "CFO / Current Liabilities",
        "value": cfo_current_liability_coverage,
        "unit": "x"
    },
    {
        "metric": "CFO Dividend Coverage",
        "value": dividend_coverage_cfo,
        "unit": "x"
    },
    {
        "metric": "FCF Dividend Coverage",
        "value": dividend_coverage_fcf,
        "unit": "x"
    },
    {
        "metric": "Dividend / FCF",
        "value": dividend_payout_of_fcf * 100,
        "unit": "%"
    }
])

# ============================================================
# LIQUIDITY STRESS TESTS
# Analytical assumptions — not forecasts
# ============================================================

scenarios = [
    {
        "scenario": "Mild Liquidity Stress",
        "investment_haircut_pct": 5.0,
        "deposit_haircut_pct": 0.0,
        "cfo_decline_pct": 10.0
    },
    {
        "scenario": "Moderate Liquidity Stress",
        "investment_haircut_pct": 10.0,
        "deposit_haircut_pct": 2.0,
        "cfo_decline_pct": 20.0
    },
    {
        "scenario": "Severe Liquidity Stress",
        "investment_haircut_pct": 20.0,
        "deposit_haircut_pct": 5.0,
        "cfo_decline_pct": 30.0
    }
]

stress_rows = []

for s in scenarios:

    stressed_investments = (
        unrestricted_investments
        * (
            1
            - s["investment_haircut_pct"] / 100
        )
    )

    stressed_deposits = (
        unrestricted_deposits
        * (
            1
            - s["deposit_haircut_pct"] / 100
        )
    )

    stressed_cfo = (
        CFO
        * (
            1
            - s["cfo_decline_pct"] / 100
        )
    )

    stressed_liquidity = (
        CASH
        + stressed_deposits
        + stressed_investments
    )

    stressed_net_liquidity = (
        stressed_liquidity
        - debt_like_obligations
    )

    stressed_liquid_coverage = (
        stressed_liquidity
        / CURRENT_LIABILITIES
    )

    stressed_dividend_coverage = (
        stressed_cfo
        / DIVIDENDS_PAID
    )

    stress_rows.append({
        **s,
        "stressed_liquidity_inr_crore":
            stressed_liquidity,
        "stressed_net_liquidity_inr_crore":
            stressed_net_liquidity,
        "liquid_asset_coverage_x":
            stressed_liquid_coverage,
        "stressed_cfo_inr_crore":
            stressed_cfo,
        "cfo_dividend_coverage_x":
            stressed_dividend_coverage
    })

stress = pd.DataFrame(stress_rows)

# ============================================================
# VALIDATION
# ============================================================

assert unrestricted_deposits == 4197.0
assert unrestricted_investments == 33273.0
assert core_liquidity == 43887.0
assert debt_like_obligations == 11409.0
assert net_liquidity == 32478.0

assert current_ratio > 1
assert liquid_asset_coverage > 0
assert dividend_coverage_cfo > 1
assert dividend_coverage_fcf > 1

assert (
    stress[
        "stressed_net_liquidity_inr_crore"
    ] > 0
).all()

# ============================================================
# SAVE
# ============================================================

output = Path("results/tables")
output.mkdir(parents=True, exist_ok=True)

kpi_path = (
    output /
    "tcs_treasury_liquidity_kpis.csv"
)

stress_path = (
    output /
    "tcs_treasury_liquidity_stress.csv"
)

kpis.round(4).to_csv(
    kpi_path,
    index=False
)

stress.round(4).to_csv(
    stress_path,
    index=False
)

# ============================================================
# PRINT
# ============================================================

print("\n" + "=" * 112)
print("FINSIGHT 360 — TCS TREASURY & LIQUIDITY ANALYSIS")
print("=" * 112)

print(
    f"\nCash & equivalents            : "
    f"₹{CASH:,.2f} Cr"
)

print(
    f"Unrestricted bank deposits    : "
    f"₹{unrestricted_deposits:,.2f} Cr"
)

print(
    f"Unrestricted investments      : "
    f"₹{unrestricted_investments:,.2f} Cr"
)

print(
    f"Core liquidity pool           : "
    f"₹{core_liquidity:,.2f} Cr"
)

print(
    f"Debt-like obligations         : "
    f"₹{debt_like_obligations:,.2f} Cr"
)

print(
    f"Net liquidity                 : "
    f"₹{net_liquidity:,.2f} Cr"
)

print("\n" + "-" * 112)
print("LIQUIDITY & CASH-FLOW KPIs")

print(
    f"Current ratio                 : "
    f"{current_ratio:.2f}x"
)

print(
    f"Cash ratio                    : "
    f"{cash_ratio:.2f}x"
)

print(
    f"Liquid asset coverage         : "
    f"{liquid_asset_coverage:.2f}x"
)

print(
    f"CFO / Current liabilities     : "
    f"{cfo_current_liability_coverage:.2f}x"
)

print(
    f"CFO dividend coverage         : "
    f"{dividend_coverage_cfo:.2f}x"
)

print(
    f"FCF dividend coverage         : "
    f"{dividend_coverage_fcf:.2f}x"
)

print(
    f"Dividend / FCF                : "
    f"{dividend_payout_of_fcf * 100:.2f}%"
)

print("\n" + "-" * 112)
print("LIQUIDITY STRESS TESTS")

for _, r in stress.iterrows():

    print(
        f"\n{r['scenario']}"
    )

    print(
        f"  Investment haircut       : "
        f"{r['investment_haircut_pct']:.0f}%"
    )

    print(
        f"  CFO decline              : "
        f"{r['cfo_decline_pct']:.0f}%"
    )

    print(
        f"  Stressed liquidity       : "
        f"₹{r['stressed_liquidity_inr_crore']:,.2f} Cr"
    )

    print(
        f"  Stressed net liquidity   : "
        f"₹{r['stressed_net_liquidity_inr_crore']:,.2f} Cr"
    )

    print(
        f"  Liquid asset coverage    : "
        f"{r['liquid_asset_coverage_x']:.2f}x"
    )

    print(
        f"  CFO dividend coverage    : "
        f"{r['cfo_dividend_coverage_x']:.2f}x"
    )

print(f"\nSaved -> {kpi_path}")
print(f"Saved -> {stress_path}")

print(
    "\nNOTE: Stress haircuts and CFO declines "
    "are analytical assumptions, not forecasts."
)

print(
    "NOTE: Restricted-purpose TCS Foundation/"
    "trust assets are excluded from available liquidity."
)

print(
    "\nTreasury and liquidity analysis "
    "completed successfully."
)
