from pathlib import Path
import re

ROOT = Path.cwd()
BASE = ROOT / "data/interim/financials/INFY"

FILES = sorted(BASE.glob(
    "balance_sheet_FY*.txt"
)) + sorted(BASE.glob(
    "profit_loss_FY*.txt"
)) + sorted(BASE.glob(
    "cash_flow_FY*.txt"
))

PATTERNS = [
    r"revenue from operations",
    r"other income",
    r"total income",
    r"employee benefit",
    r"finance cost",
    r"depreciation",
    r"profit before tax",
    r"current tax",
    r"deferred tax",
    r"profit for the year",
    r"profit attributable",
    r"basic earnings",
    r"property, plant",
    r"trade receivables",
    r"cash and cash equivalents",
    r"total current assets",
    r"total assets",
    r"trade payables",
    r"total current liabilities",
    r"total non-current liabilities",
    r"total liabilities",
    r"equity attributable",
    r"total equity",
    r"net cash generated from operating",
    r"purchase of property",
    r"purchase of intangible",
    r"net cash.*investing",
    r"net cash.*financing",
    r"dividend paid",
]

regex = re.compile("|".join(PATTERNS), re.I)

for file in FILES:

    lines = file.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    print("\n" + "=" * 100)
    print(file.name)
    print("=" * 100)

    shown = set()

    for i, line in enumerate(lines):

        if regex.search(line):

            start = max(0, i)
            end = min(len(lines), i + 6)

            key = (start, end)

            if key in shown:
                continue

            shown.add(key)

            print(f"\n--- lines {start+1}-{end} ---")

            for j in range(start, end):
                print(f"{j+1:04d}: {lines[j]}")

print("\nINFOSYS FINANCIAL LINE-ITEM SCAN COMPLETE")
