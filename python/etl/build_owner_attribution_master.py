from pathlib import Path
import pandas as pd

OUT = Path(
    "data/interim/financials/"
    "owner_attribution_FY2022_FY2026.csv"
)

rows = [
    # TCS
    ["TCS", 2022, 38327, 89139, 707],
    ["TCS", 2023, 42147, 90424, 782],
    ["TCS", 2024, 45908, 90489, 830],
    ["TCS", 2025, 48553, 94756, 1015],
    ["TCS", 2026, 49210, 107240, 1238],

    # Infosys
    ["INFY", 2022, 22110, 75350, 386],
    ["INFY", 2023, 24095, 75407, 388],
    ["INFY", 2024, 26233, 88116, 345],
    ["INFY", 2025, 26713, 95818, 385],
    ["INFY", 2026, 29440, 92852, 445],

    # HCLTech
    ["HCLTECH", 2022, 13499, 61914, 92],
    ["HCLTECH", 2023, 14851, 65405, -7],

    # FY2024 intentionally NULL:
    # exact owner PAT/equity not source-verified.
    ["HCLTECH", 2024, None, None, None],

    ["HCLTECH", 2025, 17390, 69655, 18],
    ["HCLTECH", 2026, 16642, 75165, 32],
]

df = pd.DataFrame(
    rows,
    columns=[
        "symbol",
        "fiscal_year",
        "profit_attributable_to_owners",
        "equity_attributable_to_owners",
        "non_controlling_interest",
    ],
)

# Structural validation
assert len(df) == 15
assert df[["symbol", "fiscal_year"]].duplicated().sum() == 0

assert set(df["symbol"]) == {
    "TCS",
    "INFY",
    "HCLTECH",
}

for symbol in ["TCS", "INFY", "HCLTECH"]:
    years = set(
        df.loc[
            df["symbol"] == symbol,
            "fiscal_year"
        ]
    )
    assert years == set(range(2022, 2027))

# HCL FY2024 must remain explicitly unavailable.
hcl24 = df[
    (df["symbol"] == "HCLTECH")
    & (df["fiscal_year"] == 2024)
].iloc[0]

assert pd.isna(
    hcl24["profit_attributable_to_owners"]
)
assert pd.isna(
    hcl24["equity_attributable_to_owners"]
)
assert pd.isna(
    hcl24["non_controlling_interest"]
)

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)

check = pd.read_csv(OUT)

print("=== OWNER ATTRIBUTION MASTER ===")
print(check.to_string(index=False))

print("\nRows:", len(check))
print(
    "Unique company-years:",
    check[["symbol", "fiscal_year"]]
    .drop_duplicates()
    .shape[0]
)

print("\nSaved:", OUT)
print("✓ Canonical owner-attribution master created.")
print(
    "✓ HCLTECH FY2024 remains NULL by design."
)
