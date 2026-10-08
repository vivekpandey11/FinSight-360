from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

# ------------------------------------------------------------
# Pull verified TCS market beta
# ------------------------------------------------------------

query = text("""
SELECT
    beta_vs_nifty50
FROM analytics.vw_market_risk_metrics
WHERE symbol = 'TCS';
""")

with engine.connect() as conn:
    beta = conn.execute(query).scalar()

if beta is None:
    raise ValueError("TCS beta not found")

# ------------------------------------------------------------
# DCF assumptions framework
# ------------------------------------------------------------

assumptions = pd.DataFrame([
    {
        "assumption": "Beta",
        "value": float(beta),
        "unit": "x",
        "status": "VERIFIED_INTERNAL",
        "methodology": "Historical daily-return beta vs NIFTY50 using common trading dates"
    },
    {
        "assumption": "Risk Free Rate",
        "value": None,
        "unit": "%",
        "status": "PENDING_EXTERNAL",
        "methodology": "India long-term government bond yield"
    },
    {
        "assumption": "Equity Risk Premium",
        "value": None,
        "unit": "%",
        "status": "PENDING_EXTERNAL",
        "methodology": "India market equity risk premium assumption"
    },
    {
        "assumption": "Pre-tax Cost of Debt",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "To be determined from debt / financing assumptions"
    },
    {
        "assumption": "Debt Weight",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "Capital structure assumption"
    },
    {
        "assumption": "Equity Weight",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "Capital structure assumption"
    },
    {
        "assumption": "Terminal Growth - Bear",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "Long-run nominal growth assumption"
    },
    {
        "assumption": "Terminal Growth - Base",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "Long-run nominal growth assumption"
    },
    {
        "assumption": "Terminal Growth - Bull",
        "value": None,
        "unit": "%",
        "status": "PENDING",
        "methodology": "Long-run nominal growth assumption"
    },
    {
        "assumption": "Net Cash",
        "value": None,
        "unit": "INR Crore",
        "status": "PENDING",
        "methodology": "Cash + eligible investments less debt; definition to be standardized"
    },
    {
        "assumption": "Shares Outstanding",
        "value": None,
        "unit": "Crore Shares",
        "status": "PENDING_EXTERNAL",
        "methodology": "Latest verified diluted/basic share count appropriate for valuation"
    }
])

output = Path(
    "results/tables/"
    "tcs_dcf_assumptions.csv"
)

assumptions.to_csv(
    output,
    index=False
)

print("\n" + "=" * 110)
print("FINSIGHT 360 — TCS DCF ASSUMPTION FRAMEWORK")
print("=" * 110)

print(
    assumptions.to_string(
        index=False
    )
)

print(
    f"\nVerified internal Beta = {float(beta):.4f}"
)

print(
    f"\nSaved -> {output}"
)

print(
    "\nDCF framework created successfully."
)
