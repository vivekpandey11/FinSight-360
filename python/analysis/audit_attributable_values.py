from pathlib import Path

targets = [
    # HCLTECH
    ("data/interim/financials/HCLTECH/balance_sheet_FY2023_FY2022.txt",
     ["Equity attributable to shareholders", "Non-controlling interest"]),

    ("data/interim/financials/HCLTECH/balance_sheet_FY2024_FY2023.txt",
     ["TOTAL EQUITY"]),

    ("data/interim/financials/HCLTECH/balance_sheet_FY2026_FY2025.txt",
     ["Equity attributable to owners", "Non-controlling interest"]),

    ("data/interim/financials/HCLTECH/profit_loss_FY2023_FY2022.txt",
     ["Profit for the year attributable to"]),

    ("data/interim/financials/HCLTECH/profit_loss_FY2024_FY2023.txt",
     ["Profit for the year", "attributable"]),

    ("data/interim/financials/HCLTECH/profit_loss_FY2026_FY2025.txt",
     ["Profit (loss) for the year attributable to"]),

    # INFOSYS
    ("data/interim/financials/INFY/profit_loss_FY2023_FY2022.txt",
     ["Profit attributable to:"]),

    ("data/interim/financials/INFY/profit_loss_FY2024_FY2023.txt",
     ["Profit attributable to:"]),

    ("data/interim/financials/INFY/profit_loss_FY2026_FY2025.txt",
     ["Profit attributable to:"]),

    # TCS
    ("data/interim/financials/TCS/profit_loss_FY2023_FY2022.txt",
     ["Profit for the year attributable to:"]),

    ("data/interim/financials/TCS/profit_loss_FY2024_FY2023.txt",
     ["Profit for the year attributable to:"]),

    ("data/interim/financials/TCS/profit_loss_FY2026_FY2025.txt",
     ["Profit for the year attributable to:"])
]

print("\n" + "=" * 100)
print("FINSIGHT 360 — ATTRIBUTABLE PAT / EQUITY SOURCE AUDIT")
print("=" * 100)

for filename, patterns in targets:

    path = Path(filename)

    print("\n\n" + "#" * 100)
    print(filename)
    print("#" * 100)

    if not path.exists():
        print("FILE MISSING")
        continue

    lines = path.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()

    shown = set()

    for pattern in patterns:

        for i, line in enumerate(lines):

            if pattern.lower() in line.lower():

                start = max(0, i - 4)
                end = min(len(lines), i + 9)

                key = (start, end)

                if key in shown:
                    continue

                shown.add(key)

                print(
                    f"\n--- MATCH: {pattern} "
                    f"(line {i+1}) ---"
                )

                for j in range(start, end):

                    marker = ">>" if j == i else "  "

                    print(
                        f"{marker} {j+1:5d}: "
                        f"{lines[j]}"
                    )
