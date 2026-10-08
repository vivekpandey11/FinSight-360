import pandas as pd
from pathlib import Path

# ============================================================
# INPUTS
# ============================================================

FORECAST_FILE = Path(
    "results/tables/"
    "tcs_scenario_forecast_FY2027_FY2031.csv"
)

forecast = pd.read_csv(FORECAST_FILE)

base = (
    forecast[
        forecast["scenario"] == "Base"
    ]
    .sort_values("fiscal_year")
    .copy()
)

if len(base) != 5:
    raise ValueError(
        "Expected exactly 5 Base-case forecast years."
    )

# ============================================================
# SENSITIVITY ASSUMPTIONS
# ============================================================

wacc_values = [
    0.1025,
    0.1125,
    0.1225,
    0.1325,
    0.1425
]

terminal_growth_values = [
    0.035,
    0.045,
    0.055,
    0.065,
    0.075
]

# ============================================================
# DCF FUNCTION
# ============================================================

def calculate_ev(wacc, terminal_growth):

    if wacc <= terminal_growth:
        return None

    pv_fcff = 0

    for year_number, fcff in enumerate(
        base["fcff"],
        start=1
    ):

        pv_fcff += (
            fcff /
            ((1 + wacc) ** year_number)
        )

    terminal_fcff = (
        base.iloc[-1]["fcff"]
        * (1 + terminal_growth)
    )

    terminal_value = (
        terminal_fcff /
        (wacc - terminal_growth)
    )

    pv_terminal = (
        terminal_value /
        ((1 + wacc) ** 5)
    )

    enterprise_value = (
        pv_fcff +
        pv_terminal
    )

    return enterprise_value


# ============================================================
# LONG-FORM SENSITIVITY TABLE
# ============================================================

rows = []

for wacc in wacc_values:

    for g in terminal_growth_values:

        ev = calculate_ev(
            wacc,
            g
        )

        rows.append({
            "wacc_pct":
                wacc * 100,

            "terminal_growth_pct":
                g * 100,

            "enterprise_value_inr_crore":
                ev
        })

long_df = pd.DataFrame(rows)

# ============================================================
# MATRIX
# ============================================================

matrix = (
    long_df
    .pivot(
        index="wacc_pct",
        columns="terminal_growth_pct",
        values="enterprise_value_inr_crore"
    )
)

matrix.index.name = "WACC %"

matrix.columns = [
    f"g={x:.1f}%"
    for x in matrix.columns
]

# ============================================================
# VALIDATION
# ============================================================

base_ev = calculate_ev(
    0.1225,
    0.055
)

expected_base_ev = 885220.22

difference = abs(
    base_ev -
    expected_base_ev
)

if difference > 5:
    raise ValueError(
        f"Base EV reconciliation failed. "
        f"Calculated={base_ev:.2f}, "
        f"Expected≈{expected_base_ev:.2f}"
    )

# Higher WACC should reduce valuation.

for g in terminal_growth_values:

    values = [
        calculate_ev(w, g)
        for w in wacc_values
    ]

    if not all(
        values[i] > values[i + 1]
        for i in range(
            len(values) - 1
        )
    ):
        raise ValueError(
            "WACC sensitivity validation failed."
        )

# Higher terminal growth should increase valuation.

for w in wacc_values:

    values = [
        calculate_ev(w, g)
        for g in terminal_growth_values
    ]

    if not all(
        values[i] < values[i + 1]
        for i in range(
            len(values) - 1
        )
    ):
        raise ValueError(
            "Terminal growth sensitivity validation failed."
        )

# ============================================================
# SAVE
# ============================================================

output_dir = Path(
    "results/tables"
)

long_path = (
    output_dir /
    "tcs_dcf_sensitivity_long.csv"
)

matrix_path = (
    output_dir /
    "tcs_dcf_sensitivity_matrix.csv"
)

long_df.round(2).to_csv(
    long_path,
    index=False
)

matrix.round(2).to_csv(
    matrix_path
)

# ============================================================
# PRINT
# ============================================================

print(
    "\n" +
    "=" * 100
)

print(
    "FINSIGHT 360 — TCS DCF "
    "WACC × TERMINAL GROWTH SENSITIVITY"
)

print(
    "=" * 100
)

print(
    "\nEnterprise Value (INR Crore)\n"
)

print(
    matrix.round(0)
    .to_string()
)

print(
    "\n" +
    "-" * 100
)

print(
    f"Base case reconciliation: "
    f"₹{base_ev:,.2f} crore"
)

print(
    "Base assumptions: "
    "WACC=12.25%, Terminal Growth=5.50%"
)

print(
    f"Difference vs original DCF: "
    f"₹{difference:,.2f} crore"
)

print(
    "\nVALIDATION PASSED:"
)

print(
    "✓ Higher WACC lowers valuation"
)

print(
    "✓ Higher terminal growth raises valuation"
)

print(
    "✓ Base DCF reconciles with original model"
)

print(
    f"\nSaved -> {long_path}"
)

print(
    f"Saved -> {matrix_path}"
)

print(
    "\nDCF sensitivity analysis "
    "completed successfully."
)
