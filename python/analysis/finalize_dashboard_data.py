from pathlib import Path
import pandas as pd

folder = Path("powerbi/data")
files = sorted(
    p for p in folder.glob("*.csv")
    if p.name != "dataset_manifest.csv"
)

records = []

for path in files:
    df = pd.read_csv(path)

    if df.empty:
        raise RuntimeError(f"Empty dataset: {path.name}")

    records.append({
        "dataset": path.name,
        "rows": len(df),
        "columns": len(df.columns),
        "size_kb": round(path.stat().st_size / 1024, 2)
    })

manifest = pd.DataFrame(records)

manifest.to_csv(
    folder / "dataset_manifest.csv",
    index=False
)

print("\n=== FINSIGHT 360 DASHBOARD DATA PACKAGE ===")
print(manifest.to_string(index=False))
print("\nDatasets:", len(manifest))
print("Total data rows:", manifest["rows"].sum())
print("QA PASSED")
