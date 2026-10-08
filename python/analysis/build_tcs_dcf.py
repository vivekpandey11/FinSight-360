import pandas as pd
from pathlib import Path

FORECAST = Path(
    "results/tables/"
    "tcs_scenario_forecast_FY2027_FY2031.csv"
)

df = pd.read_csv(FORECAST)

# ------------------------------------------------------------
# DCF assumptions
# ------------------------------------------------------------

WACC = 0.1225

terminal_growth = {
    "Bear": 0.045,
    "Base": 0.055,
    "Bull": 0.060
}

results = []
pv_detail = []

# ------------------------------------------------------------
# DCF engine
# ------------------------------------------------------------

for scenario in ["Bear", "Base", "Bull"]:

    temp = (
        df[df["scenario"] == scenario]
        .sort_values("fiscal_year")
        .copy()
    )

    temp["forecast_year"] = range(
        1,
        len(temp) + 1
    )

    temp["discount_factor"] = (
        1 /
        (
            (1 + WACC)
            ** temp["forecast_year"]
        )
    )

    temp["pv_fcff"] = (
        temp["fcff"]
        * temp["discount_factor"]
    )

    g = terminal_growth[scenario]

    terminal_fcff = (
        temp.iloc[-1]["fcff"]
        * (1 + g)
    )

    terminal_value = (
        terminal_fcff
        / (WACC - g)
    )

    terminal_discount_factor = (
        1 /
        (
            (1 + WACC) ** 5
        )
    )

    pv_terminal_value = (
        terminal_value
        * terminal_discount_factor
    )

    pv_explicit_fcff = (
        temp["pv_fcff"].sum()
    )

    enterprise_value = (
        pv_explicit_fcff
        + pv_terminal_value
    )

    terminal_value_pct_ev = (
        pv_terminal_value
        / enterprise_value
        * 100
    )

    results.append({
        "scenario":
            scenario,

        "wacc_pct":
            WACC * 100,

        "terminal_growth_pct":
            g * 100,

        "pv_explicit_fcff":
            pv_explicit_fcff,

        "terminal_fcff":
            terminal_fcff,

        "terminal_value":
            terminal_value,

        "pv_terminal_value":
            pv_terminal_value,

        "enterprise_value":
            enterprise_value,

        "terminal_value_pct_ev":
            terminal_value_pct_ev
    })

    for _, row in temp.iterrows():

        pv_detail.append({
            "scenario":
                scenario,

            "fiscal_year":
                int(row["fiscal_year"]),

            "fcff":
                row["fcff"],

            "discount_factor":
                row["discount_factor"],

            "pv_fcff":
                row["pv_fcff"]
        })

# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

result_df = pd.DataFrame(
    results
)

detail_df = pd.DataFrame(
    pv_detail
)

result_path = Path(
    "results/tables/"
    "tcs_dcf_enterprise_value.csv"
)

detail_path = Path(
    "results/tables/"
    "tcs_dcf_discounted_fcff.csv"
)

result_df.round(2).to_csv(
    result_path,
    index=False
)

detail_df.round(4).to_csv(
    detail_path,
    index=False
)

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert len(result_df) == 3

assert (
    result_df["enterprise_value"] > 0
).all()

assert (
    result_df["terminal_value_pct_ev"]
    .between(0, 100)
    .all()
)

assert (
    result_df.loc[
        result_df["scenario"] == "Bear",
        "enterprise_value"
    ].iloc[0]
    <
    result_df.loc[
        result_df["scenario"] == "Base",
        "enterprise_value"
    ].iloc[0]
    <
    result_df.loc[
        result_df["scenario"] == "Bull",
        "enterprise_value"
    ].iloc[0]
)

# ------------------------------------------------------------
# Print
# ------------------------------------------------------------

print(
    "\n" +
    "=" * 120
)

print(
    "FINSIGHT 360 — TCS DCF ENTERPRISE VALUE"
)

print(
    "=" * 120
)

print(
    result_df.round(2)
    .to_string(index=False)
)

print(
    "\nDiscount Rate / WACC assumption: "
    f"{WACC * 100:.2f}%"
)

print(
    "\nDCF currently stops at Enterprise Value."
)

print(
    "Net cash and shares outstanding will be "
    "applied separately to derive equity value/share."
)

print(
    f"\nSaved -> {result_path}"
)

print(
    f"Saved -> {detail_path}"
)

print(
    "\nDCF enterprise-value engine "
    "created successfully."
)
