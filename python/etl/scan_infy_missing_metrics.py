from pathlib import Path
import re

BASE = Path("data/interim/financials/INFY")

files = (
    sorted(BASE.glob("profit_loss_FY*.txt")) +
    sorted(BASE.glob("cash_flow_FY*.txt"))
)

patterns = [
    r"net cash.*operating activities",
    r"income taxes paid",
    r"dividend.*paid",
    r"dividends paid",
    r"owners of the company",
    r"equity holders of the company",
    r"basic.*earnings",
    r"earnings per equity share",
]

regex = re.compile("|".join(patterns), re.I)

for file in files:
    lines = file.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    print("\n" + "=" * 90)
    print(file.name)
    print("=" * 90)

    for i, line in enumerate(lines):
        if regex.search(line):
            start = max(0, i)
            end = min(len(lines), i + 10)

            print(f"\n--- lines {start+1}-{end} ---")
            for j in range(start, end):
                print(f"{j+1:04d}: {lines[j]}")

print("\nTARGETED INFOSYS SCAN COMPLETE")
