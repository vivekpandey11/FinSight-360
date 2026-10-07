from pathlib import Path

BASE = Path("data/interim/financials/INFY")

targets = [
    "profit_loss_FY2023_FY2022.txt",
    "profit_loss_FY2024_FY2023.txt",
    "profit_loss_FY2026_FY2025.txt",
    "cash_flow_FY2023_FY2022.txt",
    "cash_flow_FY2024_FY2023.txt",
    "cash_flow_FY2026_FY2025.txt",
]

for name in targets:
    p = BASE / name
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

    print("\n" + "=" * 90)
    print(name)
    print("=" * 90)

    for i, line in enumerate(lines):
        low = line.lower()

        if (
            "basic (" in low
            or "dividend paid" in low
            or "payment of dividend" in low
            or "dividends paid" in low
        ):
            start = max(0, i)
            end = min(len(lines), i + 14)

            for j in range(start, end):
                print(f"{j+1:04d}: {lines[j]}")

            print("-" * 50)

print("\nFINAL EPS/DIVIDEND SCAN COMPLETE")
