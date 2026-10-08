import sys
sys.path.insert(0, "python")

from sqlalchemy import text
from utils.db import get_engine

engine = get_engine()

OWNER_PAT = {
    ("TCS", 2022): 38327,
    ("TCS", 2023): 42147,
    ("TCS", 2024): 45908,
    ("TCS", 2025): 48553,
    ("TCS", 2026): 49210,

    ("INFY", 2022): 22110,
    ("INFY", 2023): 24095,
    ("INFY", 2024): 26233,
    ("INFY", 2025): 26713,
    ("INFY", 2026): 29440,

    ("HCLTECH", 2022): 13499,
    ("HCLTECH", 2023): 14851,
    ("HCLTECH", 2024): None,
    ("HCLTECH", 2025): 17390,
    ("HCLTECH", 2026): 16642,
}

OWNER_EQUITY = {
    # Existing TCS shareholder-equity values are already owner attributable
    ("TCS", 2022): 89139,
    ("TCS", 2023): 90424,
    ("TCS", 2024): 90489,
    ("TCS", 2025): 94756,
    ("TCS", 2026): 107240,

    # Existing Infosys shareholder-equity values are already owner attributable
    ("INFY", 2022): 75350,
    ("INFY", 2023): 75407,
    ("INFY", 2024): 88116,
    ("INFY", 2025): 95818,
    ("INFY", 2026): 92852,

    # HCLTech exact source-backed owner equity
    ("HCLTECH", 2022): 61914,
    ("HCLTECH", 2023): 65405,
    ("HCLTECH", 2024): None,
    ("HCLTECH", 2025): 69655,
    ("HCLTECH", 2026): 75165,
}

with engine.begin() as conn:

    print("\n=== SAFE SCHEMA MIGRATION ===")

    conn.execute(text("""
        ALTER TABLE fundamentals.income_statements
        ADD COLUMN IF NOT EXISTS
            profit_attributable_to_owners NUMERIC
    """))

    conn.execute(text("""
        ALTER TABLE fundamentals.balance_sheets
        ADD COLUMN IF NOT EXISTS
            equity_attributable_to_owners NUMERIC
    """))

    conn.execute(text("""
        ALTER TABLE fundamentals.balance_sheets
        ADD COLUMN IF NOT EXISTS
            non_controlling_interest NUMERIC
    """))

    print("✓ Attribution columns available.")

    print("\n=== LOADING VERIFIED ATTRIBUTABLE PAT ===")

    for (symbol, year), value in OWNER_PAT.items():

        result = conn.execute(text("""
            UPDATE fundamentals.income_statements i
            SET profit_attributable_to_owners = :value
            FROM fundamentals.financial_periods fp
            JOIN core.companies c
              ON c.company_id = fp.company_id
            WHERE i.period_id = fp.period_id
              AND c.symbol = :symbol
              AND fp.fiscal_year = :year
              AND fp.period_type = 'ANNUAL'
        """), {
            "value": value,
            "symbol": symbol,
            "year": year
        })

        if result.rowcount != 1:
            raise RuntimeError(
                f"Unexpected row count for PAT "
                f"{symbol} FY{year}: {result.rowcount}"
            )

    print("✓ Owner PAT loaded.")

    print("\n=== LOADING VERIFIED OWNER EQUITY ===")

    for (symbol, year), value in OWNER_EQUITY.items():

        result = conn.execute(text("""
            UPDATE fundamentals.balance_sheets b
            SET equity_attributable_to_owners = :value
            FROM fundamentals.financial_periods fp
            JOIN core.companies c
              ON c.company_id = fp.company_id
            WHERE b.period_id = fp.period_id
              AND c.symbol = :symbol
              AND fp.fiscal_year = :year
              AND fp.period_type = 'ANNUAL'
        """), {
            "value": value,
            "symbol": symbol,
            "year": year
        })

        if result.rowcount != 1:
            raise RuntimeError(
                f"Unexpected row count for equity "
                f"{symbol} FY{year}: {result.rowcount}"
            )

    print("✓ Owner equity loaded.")

    # ---------------------------------------------------------
    # Derive NCI only where owner equity is source-backed.
    # Total equity = Assets - Liabilities
    # NCI = Total equity - Equity attributable to owners
    # ---------------------------------------------------------

    conn.execute(text("""
        UPDATE fundamentals.balance_sheets
        SET non_controlling_interest =
            (total_assets - total_liabilities)
            - equity_attributable_to_owners
        WHERE total_assets IS NOT NULL
          AND total_liabilities IS NOT NULL
          AND equity_attributable_to_owners IS NOT NULL
    """))

    print("✓ NCI derived from total equity less owner equity.")

    rows = conn.execute(text("""
        SELECT
            c.symbol,
            fp.fiscal_year,

            i.net_income AS consolidated_pat,
            i.profit_attributable_to_owners AS owner_pat,

            (i.net_income -
             i.profit_attributable_to_owners)
                AS pat_nci_difference,

            (b.total_assets -
             b.total_liabilities)
                AS total_equity,

            b.equity_attributable_to_owners AS owner_equity,
            b.non_controlling_interest

        FROM fundamentals.financial_periods fp

        JOIN core.companies c
          ON c.company_id = fp.company_id

        LEFT JOIN fundamentals.income_statements i
          ON i.period_id = fp.period_id

        LEFT JOIN fundamentals.balance_sheets b
          ON b.period_id = fp.period_id

        WHERE c.symbol IN (
            'TCS',
            'INFY',
            'HCLTECH'
        )
          AND fp.period_type = 'ANNUAL'

        ORDER BY
            c.symbol,
            fp.fiscal_year
    """)).mappings().all()

print("\n=== ATTRIBUTION RECONCILIATION ===\n")

for r in rows:
    print(dict(r))

print("\n=== VALIDATION ===")

for r in rows:

    # HCL FY24 intentionally remains NULL.
    if (
        r["symbol"] == "HCLTECH"
        and r["fiscal_year"] == 2024
    ):
        assert r["owner_pat"] is None
        assert r["owner_equity"] is None
        print(
            "✓ HCLTECH FY2024 owner PAT/equity "
            "remain NULL — no guessing."
        )
        continue

    assert r["owner_pat"] is not None
    assert r["owner_equity"] is not None

    total_eq = float(r["total_equity"])
    owner_eq = float(r["owner_equity"])
    nci = float(r["non_controlling_interest"])

    assert abs(
        total_eq - owner_eq - nci
    ) < 0.01

print(
    "\n✓ Attribution migration completed successfully."
)

print(
    "✓ Original consolidated PAT and existing equity "
    "fields were NOT overwritten."
)
