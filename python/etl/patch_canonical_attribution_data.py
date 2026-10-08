from pathlib import Path
import shutil
import pandas as pd

FILES = {
    "TCS": Path(
        "data/interim/financials/TCS/"
        "TCS_fundamentals_FY2022_FY2026.csv"
    ),
    "INFY": Path(
        "data/interim/financials/INFY/"
        "INFY_fundamentals_FY2022_FY2026.csv"
    ),
    "HCLTECH": Path(
        "data/interim/financials/HCLTECH/"
        "HCLTECH_fundamentals_FY2022_FY2026.csv"
    ),
}

# Source-verified annual-report attribution values.
DATA = {
    "TCS": {
        2022: (38327, 89139, 707),
        2023: (42147, 90424, 782),
        2024: (45908, 90489, 830),
        2025: (48553, 94756, 1015),
        2026: (49210, 107240, 1238),
    },

    "INFY": {
        2022: (22110, 75350, 386),
        2023: (24095, 75407, 388),
        2024: (26233, 88116, 345),
        2025: (26713, 95818, 385),
        2026: (29440, 92852, 445),
    },

    "HCLTECH": {
        2022: (13499, 61914, 92),
        2023: (14851, 65405, -7),

        # FY2024 intentionally unavailable from verified source.
        2024: (None, None, None),

        2025: (17390, 69655, 18),
        2026: (16642, 75165, 32),
    },
}

COLS = [
    "profit_attributable_to_owners",
    "equity_attributable_to_owners",
    "non_controlling_interest",
]

print("=== CANONICAL ATTRIBUTION DATA PATCH ===")

# Fail before writing anything if expected files are absent.
missing = [
    str(path)
    for path in FILES.values()
    if not path.exists()
]

if missing:
    print("\nSTOP — missing canonical CSV:")
    for path in missing:
        print(" -", path)
    raise SystemExit(1)

for symbol, path in FILES.items():

    print(f"\n--- {symbol} ---")
    print("Source:", path)

    df = pd.read_csv(path)

    if "fiscal_year" not in df.columns:
        raise RuntimeError(
            f"{symbol}: fiscal_year column not found"
        )

    years = set(
        pd.to_numeric(
            df["fiscal_year"],
            errors="coerce"
        ).dropna().astype(int)
    )

    expected_years = set(range(2022, 2027))

    if years != expected_years:
        raise RuntimeError(
            f"{symbol}: unexpected fiscal years {sorted(years)}"
        )

    backup = path.with_suffix(".pre_attribution.csv")

    if not backup.exists():
        shutil.copy2(path, backup)
        print("Backup:", backup)
    else:
        print("Backup already exists:", backup)

    for col in COLS:
        if col not in df.columns:
            df[col] = pd.NA

    for fy, values in DATA[symbol].items():

        owner_pat, owner_equity, nci = values

        mask = (
            pd.to_numeric(
                df["fiscal_year"],
                errors="coerce"
            ) == fy
        )

        if mask.sum() != 1:
            raise RuntimeError(
                f"{symbol} FY{fy}: expected 1 row, "
                f"found {mask.sum()}"
            )

        df.loc[
            mask,
            "profit_attributable_to_owners"
        ] = owner_pat

        df.loc[
            mask,
            "equity_attributable_to_owners"
        ] = owner_equity

        df.loc[
            mask,
            "non_controlling_interest"
        ] = nci

    # Reconciliation:
    # total equity = owner equity + NCI
    if "shareholders_equity" in df.columns:

        for _, row in df.iterrows():

            fy = int(row["fiscal_year"])
            owner_eq = row[
                "equity_attributable_to_owners"
            ]
            nci = row["non_controlling_interest"]

            if pd.isna(owner_eq) or pd.isna(nci):
                continue

            # Existing HCL shareholders_equity is total equity.
            # TCS/INFY legacy shareholders_equity is owner equity,
            # so only enforce total-equity reconciliation for HCL.
            if symbol == "HCLTECH":
                legacy_total = row["shareholders_equity"]

                if (
                    not pd.isna(legacy_total)
                    and abs(
                        float(legacy_total)
                        - (
                            float(owner_eq)
                            + float(nci)
                        )
                    ) > 0.01
                ):
                    raise RuntimeError(
                        f"{symbol} FY{fy}: "
                        "equity reconciliation failed"
                    )

    df.to_csv(path, index=False)

    check = pd.read_csv(path)

    print(
        check[
            [
                "fiscal_year",
                "profit_attributable_to_owners",
                "equity_attributable_to_owners",
                "non_controlling_interest",
            ]
        ].to_string(index=False)
    )

print("\n✓ Canonical attribution CSV patch completed.")
print("✓ HCLTECH FY2024 intentionally remains NULL.")
