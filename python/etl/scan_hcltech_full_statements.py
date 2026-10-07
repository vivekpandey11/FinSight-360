from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "data/interim/financials/HCLTECH"

FILES = [
    "balance_sheet_FY2026_FY2025.txt",
    "profit_loss_FY2026_FY2025.txt",
    "cash_flow_FY2026_FY2025.txt",

    "balance_sheet_FY2024_FY2023.txt",
    "profit_loss_FY2024_FY2023.txt",
    "cash_flow_FY2024_FY2023.txt",
]

# Print complete extracted statements with line numbers.
# These files are small enough that this is safer than trying to
# interpret garbled HCLTech PDF labels using regex alone.

for name in FILES:

    path = BASE / name

    print("\n" + "=" * 105)
    print(name)
    print("=" * 105)

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    lines = path.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    for i, line in enumerate(lines, start=1):
        if line.strip():
            print(f"{i:04d}: {line}")

print("\nHCLTECH FULL STATEMENT SCAN COMPLETE")
