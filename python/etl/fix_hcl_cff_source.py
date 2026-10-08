from pathlib import Path
import pandas as pd
import shutil

path = Path(
    "data/interim/financials/HCLTECH/"
    "HCLTECH_fundamentals_FY2022_FY2026.csv"
)

df = pd.read_csv(path)

print("=== HCL FY2024 SOURCE RECONCILIATION ===")
print("Columns:", list(df.columns))

required = {"fiscal_year", "financing_cash_flow"}
missing = required - set(df.columns)

if missing:
    raise RuntimeError(
        f"STOP: Missing columns {sorted(missing)}"
    )

mask = pd.to_numeric(
    df["fiscal_year"], errors="coerce"
) == 2024

if mask.sum() != 1:
    raise RuntimeError(
        "STOP: Expected exactly one FY2024 row."
    )

old_value = df.loc[mask, "financing_cash_flow"].iloc[0]

if pd.notna(old_value) and float(old_value) != -15464:
    raise RuntimeError(
        f"STOP: Existing CFF conflicts: {old_value}"
    )

backup = path.with_suffix(".pre_cff_fix.csv")

if not backup.exists():
    shutil.copy2(path, backup)

df.loc[mask, "financing_cash_flow"] = -15464

df.to_csv(path, index=False)

check = pd.read_csv(path)
value = check.loc[
    pd.to_numeric(
        check["fiscal_year"], errors="coerce"
    ) == 2024,
    "financing_cash_flow"
].iloc[0]

assert float(value) == -15464

print("Previous CFF:", old_value)
print("Canonical FY2024 CFF:", value)
print("Backup:", backup)
print("PASS: HCL FY2024 CFF source updated.")

