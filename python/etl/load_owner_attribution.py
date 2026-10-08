from pathlib import Path

import pandas as pd
from sqlalchemy import text

from utils.db import get_engine


CSV = Path(
    "data/interim/financials/"
    "owner_attribution_FY2022_FY2026.csv"
)


def clean(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


if not CSV.exists():
    raise FileNotFoundError(
        f"Owner attribution master not found: {CSV}"
    )


df = pd.read_csv(CSV)

required_columns = {
    "symbol",
    "fiscal_year",
    "profit_attributable_to_owners",
    "equity_attributable_to_owners",
    "non_controlling_interest",
}

missing = required_columns - set(df.columns)

if missing:
    raise RuntimeError(
        f"Missing required columns: {sorted(missing)}"
    )


# --------------------------------------------------
# Structural validation
# --------------------------------------------------

if len(df) != 15:
    raise RuntimeError(
        f"Expected 15 company-years, found {len(df)}"
    )

if df[["symbol", "fiscal_year"]].duplicated().any():
    raise RuntimeError(
        "Duplicate symbol/fiscal_year rows found"
    )


engine = get_engine()

print("=== OWNER ATTRIBUTION DB LOAD ===")


with engine.begin() as conn:

    # Ensure columns exist even on an older database.
    conn.execute(text("""
        ALTER TABLE fundamentals.income_statements
        ADD COLUMN IF NOT EXISTS
        profit_attributable_to_owners NUMERIC(20,2)
    """))

    conn.execute(text("""
        ALTER TABLE fundamentals.balance_sheets
        ADD COLUMN IF NOT EXISTS
        equity_attributable_to_owners NUMERIC(20,2)
    """))

    conn.execute(text("""
        ALTER TABLE fundamentals.balance_sheets
        ADD COLUMN IF NOT EXISTS
        non_controlling_interest NUMERIC(20,2)
    """))

    updated = 0

    for _, row in df.iterrows():

        symbol = str(row["symbol"])
        fiscal_year = int(row["fiscal_year"])

        period = conn.execute(
            text("""
                SELECT fp.period_id
                FROM fundamentals.financial_periods fp
                JOIN core.companies c
                  ON c.company_id = fp.company_id
                WHERE c.symbol = :symbol
                  AND fp.fiscal_year = :fy
                  AND fp.period_type = 'ANNUAL'
                LIMIT 1
            """),
            {
                "symbol": symbol,
                "fy": fiscal_year,
            }
        ).scalar_one_or_none()

        if period is None:
            raise RuntimeError(
                f"{symbol} FY{fiscal_year}: "
                "annual period not found"
            )

        income_exists = conn.execute(
            text("""
                SELECT 1
                FROM fundamentals.income_statements
                WHERE period_id = :pid
            """),
            {"pid": period}
        ).scalar_one_or_none()

        balance_exists = conn.execute(
            text("""
                SELECT 1
                FROM fundamentals.balance_sheets
                WHERE period_id = :pid
            """),
            {"pid": period}
        ).scalar_one_or_none()

        if income_exists is None:
            raise RuntimeError(
                f"{symbol} FY{fiscal_year}: "
                "income statement missing"
            )

        if balance_exists is None:
            raise RuntimeError(
                f"{symbol} FY{fiscal_year}: "
                "balance sheet missing"
            )

        conn.execute(
            text("""
                UPDATE fundamentals.income_statements
                SET profit_attributable_to_owners = :owner_pat
                WHERE period_id = :pid
            """),
            {
                "owner_pat": clean(
                    row["profit_attributable_to_owners"]
                ),
                "pid": period,
            }
        )

        conn.execute(
            text("""
                UPDATE fundamentals.balance_sheets
                SET
                    equity_attributable_to_owners =
                        :owner_equity,
                    non_controlling_interest =
                        :nci
                WHERE period_id = :pid
            """),
            {
                "owner_equity": clean(
                    row["equity_attributable_to_owners"]
                ),
                "nci": clean(
                    row["non_controlling_interest"]
                ),
                "pid": period,
            }
        )

        updated += 1


print(f"Updated company-years: {updated}")


# --------------------------------------------------
# DB reconciliation
# --------------------------------------------------

validation_sql = text("""
SELECT
    c.symbol,
    fp.fiscal_year,

    i.net_income AS consolidated_pat,
    i.profit_attributable_to_owners AS owner_pat,

    b.shareholders_equity AS legacy_equity,
    b.equity_attributable_to_owners AS owner_equity,
    b.non_controlling_interest AS nci,

    b.total_assets,
    b.total_liabilities,

    ROUND(
        b.total_assets - b.total_liabilities,
        2
    ) AS implied_total_equity

FROM fundamentals.financial_periods fp

JOIN core.companies c
  ON c.company_id = fp.company_id

JOIN fundamentals.income_statements i
  ON i.period_id = fp.period_id

JOIN fundamentals.balance_sheets b
  ON b.period_id = fp.period_id

WHERE fp.period_type = 'ANNUAL'
  AND fp.fiscal_year BETWEEN 2022 AND 2026
  AND c.symbol IN ('TCS', 'INFY', 'HCLTECH')

ORDER BY c.symbol, fp.fiscal_year
""")


with engine.connect() as conn:
    rows = conn.execute(
        validation_sql
    ).mappings().all()


if len(rows) != 15:
    raise RuntimeError(
        f"Expected 15 validation rows, found {len(rows)}"
    )


print("\n=== DB RECONCILIATION ===")

valid_attribution_rows = 0

for row in rows:

    symbol = row["symbol"]
    fy = row["fiscal_year"]

    owner_pat = row["owner_pat"]
    owner_equity = row["owner_equity"]
    nci = row["nci"]
    total_equity = row["implied_total_equity"]

    print(dict(row))

    # HCL FY2024 is intentionally unavailable.
    if symbol == "HCLTECH" and fy == 2024:

        if (
            owner_pat is not None
            or owner_equity is not None
            or nci is not None
        ):
            raise RuntimeError(
                "HCLTECH FY2024 attribution "
                "must remain NULL"
            )

        continue

    if (
        owner_pat is None
        or owner_equity is None
        or nci is None
    ):
        raise RuntimeError(
            f"{symbol} FY{fy}: "
            "unexpected NULL attribution"
        )

    # Owner equity + NCI must equal consolidated equity.
    difference = abs(
        float(owner_equity)
        + float(nci)
        - float(total_equity)
    )

    if difference > 0.01:
        raise RuntimeError(
            f"{symbol} FY{fy}: "
            f"equity reconciliation failed "
            f"(difference={difference})"
        )

    valid_attribution_rows += 1


if valid_attribution_rows != 14:
    raise RuntimeError(
        "Expected 14 source-verified "
        f"attribution rows, got {valid_attribution_rows}"
    )


print("\n✓ 15 company-years loaded.")
print("✓ 14 company-years fully source-verified.")
print("✓ HCLTECH FY2024 remains NULL by design.")
print("✓ Owner equity + NCI reconciles to total equity.")
print("✓ Owner attribution DB load PASSED.")
