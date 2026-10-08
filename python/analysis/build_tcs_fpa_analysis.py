import pandas as pd
from pathlib import Path

# ============================================================
# LOAD DATA
# ============================================================

hist = pd.read_csv(
    "results/tables/tcs_historical_financial_model_base.csv"
)

forecast = pd.read_csv(
    "results/tables/tcs_scenario_forecast_FY2027_FY2031.csv"
)

actual = hist[
    hist["fiscal_year"] == 2026
].iloc[0]

budget = forecast[
    (forecast["scenario"] == "Base")
    & (forecast["fiscal_year"] == 2027)
].iloc[0]

# ============================================================
# ACTUAL VS BASE BUDGET
# ============================================================

comparison = [
    (
        "Revenue",
        float(actual["revenue"]),
        float(budget["revenue"])
    ),
    (
        "EBIT",
        float(actual["ebit"]),
        float(budget["ebit"])
    ),
    (
        "FCF / FCFF",
        float(actual["fcf"]),
        float(budget["fcff"])
    )
]

rows = []

for metric, actual_value, budget_value in comparison:

    variance = (
        budget_value - actual_value
    )

    variance_pct = (
        variance / actual_value
    ) * 100

    rows.append({
        "metric": metric,
        "fy2026_actual":
            actual_value,
        "fy2027_base_budget":
            budget_value,
        "variance_inr_crore":
            variance,
        "variance_pct":
            variance_pct
    })

variance_df = pd.DataFrame(rows)

# ============================================================
# MARGIN BRIDGE
# ============================================================

actual_revenue = float(
    actual["revenue"]
)

budget_revenue = float(
    budget["revenue"]
)

actual_ebit_margin = float(
    actual["ebit_margin_pct"]
)

budget_ebit_margin = float(
    budget["ebit_margin_pct"]
)

actual_fcf_margin = float(
    actual["fcf_margin_pct"]
)

budget_fcff_margin = float(
    budget["fcff_margin_pct"]
)

margin_df = pd.DataFrame([
    {
        "metric":
            "EBIT Margin",

        "fy2026_actual_pct":
            actual_ebit_margin,

        "fy2027_budget_pct":
            budget_ebit_margin,

        "change_bps":
            (
                budget_ebit_margin
                - actual_ebit_margin
            ) * 100
    },
    {
        "metric":
            "FCF / FCFF Margin",

        "fy2026_actual_pct":
            actual_fcf_margin,

        "fy2027_budget_pct":
            budget_fcff_margin,

        "change_bps":
            (
                budget_fcff_margin
                - actual_fcf_margin
            ) * 100
    }
])

# ============================================================
# FY2027 BUDGET DRIVERS
# ============================================================

revenue_growth = float(
    budget["revenue_growth_pct"]
)

tax_rate = float(
    budget["tax_rate_pct"]
)

da_pct_revenue = (
    float(budget["da"])
    / budget_revenue
) * 100

capex_pct_revenue = (
    float(budget["capex"])
    / budget_revenue
) * 100

delta_nwc_pct_revenue = (
    float(budget["delta_nwc"])
    / budget_revenue
) * 100

driver_df = pd.DataFrame([
    {
        "driver":
            "Revenue Growth",
        "value":
            revenue_growth,
        "unit":
            "%"
    },
    {
        "driver":
            "EBIT Margin",
        "value":
            budget_ebit_margin,
        "unit":
            "%"
    },
    {
        "driver":
            "Tax Rate",
        "value":
            tax_rate,
        "unit":
            "%"
    },
    {
        "driver":
            "D&A / Revenue",
        "value":
            da_pct_revenue,
        "unit":
            "%"
    },
    {
        "driver":
            "CapEx / Revenue",
        "value":
            capex_pct_revenue,
        "unit":
            "%"
    },
    {
        "driver":
            "Delta NWC / Revenue",
        "value":
            delta_nwc_pct_revenue,
        "unit":
            "%"
    }
])

# ============================================================
# MANAGEMENT-STYLE KPI SUMMARY
# ============================================================

kpi_df = pd.DataFrame([{
    "fy2027_revenue_growth_pct":
        revenue_growth,

    "fy2027_ebit_growth_pct":
        (
            float(budget["ebit"])
            / float(actual["ebit"])
            - 1
        ) * 100,

    "ebit_margin_change_bps":
        (
            budget_ebit_margin
            - actual_ebit_margin
        ) * 100,

    "fcf_fcff_margin_change_bps":
        (
            budget_fcff_margin
            - actual_fcf_margin
        ) * 100,

    "fy2027_fcff_inr_crore":
        float(budget["fcff"])
}])

# ============================================================
# VALIDATION
# ============================================================

assert budget_revenue > actual_revenue

assert abs(
    revenue_growth - 6.0
) < 0.01

assert abs(
    budget_ebit_margin - 26.7
) < 0.01

assert abs(
    tax_rate - 25.3
) < 0.01

assert abs(
    da_pct_revenue - 2.15
) < 0.01

assert abs(
    capex_pct_revenue - 1.40
) < 0.01

assert abs(
    delta_nwc_pct_revenue - 0.70
) < 0.01

# ============================================================
# SAVE
# ============================================================

output = Path(
    "results/tables"
)

variance_path = (
    output /
    "tcs_fpa_budget_variance.csv"
)

margin_path = (
    output /
    "tcs_fpa_margin_bridge.csv"
)

driver_path = (
    output /
    "tcs_fpa_budget_drivers.csv"
)

kpi_path = (
    output /
    "tcs_fpa_management_kpis.csv"
)

variance_df.round(2).to_csv(
    variance_path,
    index=False
)

margin_df.round(2).to_csv(
    margin_path,
    index=False
)

driver_df.round(2).to_csv(
    driver_path,
    index=False
)

kpi_df.round(2).to_csv(
    kpi_path,
    index=False
)

# ============================================================
# PRINT
# ============================================================

print("\n" + "=" * 112)

print(
    "FINSIGHT 360 — TCS FP&A "
    "FY2027 BASE-CASE BUDGET"
)

print("=" * 112)

print(
    "\nFY2026 ACTUAL -> FY2027 BASE BUDGET"
)

print("-" * 112)

for _, r in variance_df.iterrows():

    print(
        f"{r['metric']:16s} | "
        f"Actual ₹{r['fy2026_actual']:,.2f} Cr | "
        f"Budget ₹{r['fy2027_base_budget']:,.2f} Cr | "
        f"Variance ₹{r['variance_inr_crore']:+,.2f} Cr | "
        f"{r['variance_pct']:+.2f}%"
    )

print("\n" + "-" * 112)

print("MARGIN BRIDGE")

for _, r in margin_df.iterrows():

    print(
        f"{r['metric']:20s} | "
        f"FY26 {r['fy2026_actual_pct']:.2f}% | "
        f"FY27 {r['fy2027_budget_pct']:.2f}% | "
        f"Change {r['change_bps']:+.0f} bps"
    )

print("\n" + "-" * 112)

print("FY2027 BASE-CASE BUDGET DRIVERS")

for _, r in driver_df.iterrows():

    print(
        f"{r['driver']:25s}: "
        f"{r['value']:.2f}{r['unit']}"
    )

print("\n" + "-" * 112)

print("MANAGEMENT KPI VIEW")

for col, value in kpi_df.iloc[0].items():

    print(
        f"{col:35s}: "
        f"{value:,.2f}"
    )

print(f"\nSaved -> {variance_path}")
print(f"Saved -> {margin_path}")
print(f"Saved -> {driver_path}")
print(f"Saved -> {kpi_path}")

print(
    "\nNOTE 1: FY2027 Base is an internal "
    "analytical budget, not TCS management guidance."
)

print(
    "NOTE 2: FY2026 FCF and FY2027 FCFF are "
    "different cash-flow concepts; comparison is "
    "shown as a planning bridge, not accounting variance."
)

print(
    "\nFP&A analysis completed successfully."
)
