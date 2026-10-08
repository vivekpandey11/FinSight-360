import pandas as pd
from pathlib import Path

BASE_FILE = Path(
    "results/tables/"
    "tcs_historical_financial_model_base.csv"
)

df = pd.read_csv(BASE_FILE)

latest = df.loc[
    df["fiscal_year"] == 2026
].iloc[0]

# ============================================================
# FORECAST ASSUMPTIONS
# ============================================================

scenarios = {

    "Bear": {
        "revenue_growth": [
            0.03, 0.035, 0.04, 0.04, 0.04
        ],
        "ebit_margin": [
            0.255, 0.255, 0.258, 0.260, 0.260
        ],
        "tax_rate": 0.255,
        "da_pct_revenue": 0.021,
        "capex_pct_revenue": 0.016,
        "nwc_investment_pct_revenue": 0.010
    },

    "Base": {
        "revenue_growth": [
            0.06, 0.065, 0.07, 0.07, 0.07
        ],
        "ebit_margin": [
            0.267, 0.268, 0.270, 0.270, 0.270
        ],
        "tax_rate": 0.253,
        "da_pct_revenue": 0.0215,
        "capex_pct_revenue": 0.014,
        "nwc_investment_pct_revenue": 0.007
    },

    "Bull": {
        "revenue_growth": [
            0.09, 0.095, 0.10, 0.10, 0.095
        ],
        "ebit_margin": [
            0.275, 0.278, 0.280, 0.282, 0.282
        ],
        "tax_rate": 0.250,
        "da_pct_revenue": 0.022,
        "capex_pct_revenue": 0.013,
        "nwc_investment_pct_revenue": 0.005
    }
}

# ============================================================
# FORECAST ENGINE
# ============================================================

forecast_rows = []

for scenario, assumptions in scenarios.items():

    previous_revenue = float(
        latest["revenue"]
    )

    for index, year in enumerate(
        range(2027, 2032)
    ):

        growth = assumptions[
            "revenue_growth"
        ][index]

        revenue = (
            previous_revenue *
            (1 + growth)
        )

        ebit_margin = assumptions[
            "ebit_margin"
        ][index]

        ebit = (
            revenue *
            ebit_margin
        )

        tax_rate = assumptions[
            "tax_rate"
        ]

        nopat = (
            ebit *
            (1 - tax_rate)
        )

        da = (
            revenue *
            assumptions[
                "da_pct_revenue"
            ]
        )

        capex = (
            revenue *
            assumptions[
                "capex_pct_revenue"
            ]
        )

        # Simplified analytical NWC investment assumption.
        delta_nwc = (
            revenue *
            assumptions[
                "nwc_investment_pct_revenue"
            ]
        )

        fcff = (
            nopat
            + da
            - capex
            - delta_nwc
        )

        forecast_rows.append({

            "scenario":
                scenario,

            "fiscal_year":
                year,

            "revenue":
                revenue,

            "revenue_growth_pct":
                growth * 100,

            "ebit_margin_pct":
                ebit_margin * 100,

            "ebit":
                ebit,

            "tax_rate_pct":
                tax_rate * 100,

            "nopat":
                nopat,

            "da":
                da,

            "capex":
                capex,

            "delta_nwc":
                delta_nwc,

            "fcff":
                fcff,

            "fcff_margin_pct":
                (
                    fcff /
                    revenue * 100
                )
        })

        previous_revenue = revenue

forecast = pd.DataFrame(
    forecast_rows
)

# ============================================================
# VALIDATION
# ============================================================

assert len(forecast) == 15

assert (
    forecast["revenue"] > 0
).all()

assert (
    forecast["ebit"] > 0
).all()

assert (
    forecast["fcff"] > 0
).all()

assert (
    forecast["scenario"]
    .value_counts()
    .eq(5)
    .all()
)

# ============================================================
# OUTPUT
# ============================================================

output = Path(
    "results/tables/"
    "tcs_scenario_forecast_FY2027_FY2031.csv"
)

forecast.round(2).to_csv(
    output,
    index=False
)

print(
    "\n" +
    "=" * 130
)

print(
    "FINSIGHT 360 — TCS "
    "FY2027-FY2031 SCENARIO FORECAST"
)

print(
    "=" * 130
)

for scenario in [
    "Bear",
    "Base",
    "Bull"
]:

    print(
        f"\n{scenario.upper()} CASE"
    )

    print("-" * 105)

    temp = forecast[
        forecast["scenario"]
        == scenario
    ].copy()

    print(
        temp[
            [
                "fiscal_year",
                "revenue",
                "revenue_growth_pct",
                "ebit_margin_pct",
                "ebit",
                "nopat",
                "capex",
                "delta_nwc",
                "fcff",
                "fcff_margin_pct"
            ]
        ]
        .round(2)
        .to_string(
            index=False
        )
    )

print(
    "\n" +
    "=" * 130
)

print(
    "VALIDATION PASSED: "
    "15 forecast observations "
    "(3 scenarios x 5 years)"
)

print(
    f"\nSaved -> {output}"
)

print(
    "\nTCS scenario forecast "
    "created successfully."
)
