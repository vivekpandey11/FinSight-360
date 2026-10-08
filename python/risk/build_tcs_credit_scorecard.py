import pandas as pd
from pathlib import Path

# ============================================================
# FY2026 TCS VERIFIED / MODEL DATA
# INR CRORE
# ============================================================

REVENUE = 267021.0
EBITDA = 76800.0
EBIT = 71240.0
NET_INCOME = 49454.0

TOTAL_ASSETS = 182372.0
TOTAL_LIABILITIES = 73894.0
SHAREHOLDERS_EQUITY = 107240.0

CURRENT_ASSETS = 135705.0
CURRENT_LIABILITIES = 60914.0

CFO = 52094.0
FCF = 48057.0

FINANCE_COST = 1227.0

CORE_LIQUIDITY = 43887.0
DEBT_LIKE_OBLIGATIONS = 11409.0
NET_LIQUIDITY = 32478.0

# ============================================================
# CREDIT METRICS
# ============================================================

current_ratio = (
    CURRENT_ASSETS / CURRENT_LIABILITIES
)

liabilities_to_equity = (
    TOTAL_LIABILITIES / SHAREHOLDERS_EQUITY
)

debt_like_to_ebitda = (
    DEBT_LIKE_OBLIGATIONS / EBITDA
)

net_liquidity_to_ebitda = (
    NET_LIQUIDITY / EBITDA
)

ebit_interest_coverage = (
    EBIT / FINANCE_COST
)

cfo_to_liabilities = (
    CFO / TOTAL_LIABILITIES
)

fcf_to_liabilities = (
    FCF / TOTAL_LIABILITIES
)

ebitda_margin = (
    EBITDA / REVENUE
)

net_margin = (
    NET_INCOME / REVENUE
)

core_liquidity_to_current_liabilities = (
    CORE_LIQUIDITY / CURRENT_LIABILITIES
)

# ============================================================
# SCORECARD
# 1 = weak, 5 = strong
# Internal analytical score only.
# ============================================================

def score_current_ratio(x):
    if x >= 2.0:
        return 5
    if x >= 1.5:
        return 4
    if x >= 1.2:
        return 3
    if x >= 1.0:
        return 2
    return 1


def score_liabilities_equity(x):
    if x <= 0.75:
        return 5
    if x <= 1.00:
        return 4
    if x <= 1.50:
        return 3
    if x <= 2.00:
        return 2
    return 1


def score_debt_ebitda(x):
    if x <= 0.50:
        return 5
    if x <= 1.00:
        return 4
    if x <= 2.00:
        return 3
    if x <= 3.00:
        return 2
    return 1


def score_interest_coverage(x):
    if x >= 10:
        return 5
    if x >= 6:
        return 4
    if x >= 3:
        return 3
    if x >= 1.5:
        return 2
    return 1


def score_cfo_liabilities(x):
    if x >= 0.50:
        return 5
    if x >= 0.35:
        return 4
    if x >= 0.20:
        return 3
    if x >= 0.10:
        return 2
    return 1


def score_ebitda_margin(x):
    if x >= 0.25:
        return 5
    if x >= 0.20:
        return 4
    if x >= 0.15:
        return 3
    if x >= 0.10:
        return 2
    return 1


def score_liquid_coverage(x):
    if x >= 0.75:
        return 5
    if x >= 0.50:
        return 4
    if x >= 0.30:
        return 3
    if x >= 0.15:
        return 2
    return 1


metrics = [
    {
        "metric": "Current Ratio",
        "value": current_ratio,
        "unit": "x",
        "score": score_current_ratio(current_ratio),
        "weight_pct": 15
    },
    {
        "metric": "Liabilities / Equity",
        "value": liabilities_to_equity,
        "unit": "x",
        "score": score_liabilities_equity(
            liabilities_to_equity
        ),
        "weight_pct": 10
    },
    {
        "metric": "Debt-like Obligations / EBITDA",
        "value": debt_like_to_ebitda,
        "unit": "x",
        "score": score_debt_ebitda(
            debt_like_to_ebitda
        ),
        "weight_pct": 20
    },
    {
        "metric": "EBIT / Finance Cost",
        "value": ebit_interest_coverage,
        "unit": "x",
        "score": score_interest_coverage(
            ebit_interest_coverage
        ),
        "weight_pct": 20
    },
    {
        "metric": "CFO / Total Liabilities",
        "value": cfo_to_liabilities,
        "unit": "x",
        "score": score_cfo_liabilities(
            cfo_to_liabilities
        ),
        "weight_pct": 15
    },
    {
        "metric": "EBITDA Margin",
        "value": ebitda_margin * 100,
        "unit": "%",
        "score": score_ebitda_margin(
            ebitda_margin
        ),
        "weight_pct": 10
    },
    {
        "metric": "Liquid Assets / Current Liabilities",
        "value":
            core_liquidity_to_current_liabilities,
        "unit": "x",
        "score": score_liquid_coverage(
            core_liquidity_to_current_liabilities
        ),
        "weight_pct": 10
    }
]

scorecard = pd.DataFrame(metrics)

scorecard["weighted_score"] = (
    scorecard["score"]
    * scorecard["weight_pct"]
    / 100
)

total_score = (
    scorecard["weighted_score"].sum()
)

score_pct = (
    total_score / 5
) * 100

# ============================================================
# INTERNAL RISK BAND
# ============================================================

if score_pct >= 85:
    risk_band = "Low Credit Risk"
elif score_pct >= 70:
    risk_band = "Moderate-Low Credit Risk"
elif score_pct >= 55:
    risk_band = "Moderate Credit Risk"
elif score_pct >= 40:
    risk_band = "Elevated Credit Risk"
else:
    risk_band = "High Credit Risk"

# ============================================================
# SUMMARY
# ============================================================

summary = pd.DataFrame([{
    "company": "TCS",
    "fiscal_year": 2026,
    "weighted_score_out_of_5":
        total_score,
    "score_pct":
        score_pct,
    "internal_risk_band":
        risk_band,
    "current_ratio":
        current_ratio,
    "debt_like_to_ebitda":
        debt_like_to_ebitda,
    "ebit_interest_coverage":
        ebit_interest_coverage,
    "cfo_to_total_liabilities":
        cfo_to_liabilities,
    "fcf_to_total_liabilities":
        fcf_to_liabilities,
    "net_liquidity_to_ebitda":
        net_liquidity_to_ebitda,
    "ebitda_margin_pct":
        ebitda_margin * 100,
    "net_margin_pct":
        net_margin * 100
}])

# ============================================================
# VALIDATION
# ============================================================

assert scorecard["weight_pct"].sum() == 100
assert scorecard["score"].between(1, 5).all()

assert total_score >= 1
assert total_score <= 5

assert current_ratio > 0
assert debt_like_to_ebitda >= 0
assert ebit_interest_coverage > 0

# ============================================================
# SAVE
# ============================================================

output = Path("results/tables")
output.mkdir(parents=True, exist_ok=True)

scorecard_path = (
    output /
    "tcs_credit_scorecard.csv"
)

summary_path = (
    output /
    "tcs_credit_risk_summary.csv"
)

scorecard.round(4).to_csv(
    scorecard_path,
    index=False
)

summary.round(4).to_csv(
    summary_path,
    index=False
)

# ============================================================
# PRINT
# ============================================================

print("\n" + "=" * 116)

print(
    "FINSIGHT 360 — TCS CORPORATE "
    "CREDIT ANALYSIS"
)

print("=" * 116)

for _, r in scorecard.iterrows():

    print(
        f"\n{r['metric']}"
        f"\n  Value          : "
        f"{r['value']:.2f}{r['unit']}"
        f"\n  Score          : "
        f"{int(r['score'])}/5"
        f"\n  Weight         : "
        f"{r['weight_pct']:.0f}%"
        f"\n  Weighted Score : "
        f"{r['weighted_score']:.2f}"
    )

print("\n" + "-" * 116)

print(
    f"Weighted Credit Score : "
    f"{total_score:.2f}/5.00"
)

print(
    f"Normalized Score      : "
    f"{score_pct:.2f}%"
)

print(
    f"Internal Risk Band    : "
    f"{risk_band}"
)

print("\n" + "-" * 116)

print("SUPPORTING CREDIT METRICS")

print(
    f"FCF / Total liabilities       : "
    f"{fcf_to_liabilities:.2f}x"
)

print(
    f"Net liquidity / EBITDA        : "
    f"{net_liquidity_to_ebitda:.2f}x"
)

print(
    f"Net margin                    : "
    f"{net_margin * 100:.2f}%"
)

print(f"\nSaved -> {scorecard_path}")
print(f"Saved -> {summary_path}")

print(
    "\nIMPORTANT: This is an internal analytical "
    "scorecard for the FinSight 360 project."
)

print(
    "It is NOT an external credit rating and must "
    "not be presented as a CRISIL/ICRA/S&P/Moody's rating."
)

print(
    "\nCorporate credit analysis "
    "completed successfully."
)
