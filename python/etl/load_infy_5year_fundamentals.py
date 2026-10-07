from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

ROOT = Path.cwd()
CSV = ROOT / "data/interim/financials/INFY/INFY_fundamentals_FY2022_FY2026.csv"

df = pd.read_csv(CSV)

def pyval(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value

engine = get_engine()

with engine.begin() as conn:

    # -------------------------------------------------
    # COMPANY
    # -------------------------------------------------
    company_id = conn.execute(
        text("""
            SELECT company_id
            FROM core.companies
            WHERE symbol = 'INFY'
            LIMIT 1
        """)
    ).scalar()

    if company_id is None:
        raise ValueError(
            "INFY not found in core.companies"
        )

    print(f"INFY company_id: {company_id}")

    # -------------------------------------------------
    # LOAD FY2022-FY2026
    # -------------------------------------------------
    for _, raw_row in df.iterrows():

        row = raw_row.map(pyval)

        fiscal_year = int(row["fiscal_year"])

        # ---------------- PERIOD ----------------

        period_id = conn.execute(
            text("""
                SELECT period_id
                FROM fundamentals.financial_periods
                WHERE company_id = :company_id
                  AND fiscal_year = :fiscal_year
                  AND period_type = 'ANNUAL'
                LIMIT 1
            """),
            {
                "company_id": company_id,
                "fiscal_year": fiscal_year,
            },
        ).scalar()

        if period_id is None:

            period_id = conn.execute(
                text("""
                    INSERT INTO fundamentals.financial_periods
                    (
                        company_id,
                        fiscal_year,
                        period_type,
                        period_end_date,
                        currency,
                        unit_scale
                    )
                    VALUES
                    (
                        :company_id,
                        :fiscal_year,
                        'ANNUAL',
                        :period_end_date,
                        'INR',
                        'CRORE'
                    )
                    RETURNING period_id
                """),
                {
                    "company_id": company_id,
                    "fiscal_year": fiscal_year,
                    "period_end_date": row["period_end"],
                },
            ).scalar()

        # ---------------- INCOME STATEMENT ----------------

        conn.execute(
            text("""
                DELETE FROM fundamentals.income_statements
                WHERE period_id = :period_id
            """),
            {"period_id": period_id},
        )

        conn.execute(
            text("""
                INSERT INTO fundamentals.income_statements
                (
                    period_id,
                    revenue,
                    operating_expenses,
                    ebitda,
                    depreciation_amortization,
                    ebit,
                    finance_cost,
                    profit_before_tax,
                    tax_expense,
                    net_income,
                    eps
                )
                VALUES
                (
                    :period_id,
                    :revenue,
                    NULL,
                    :ebitda,
                    :da,
                    :ebit,
                    :finance_cost,
                    :pbt,
                    :tax_expense,
                    :net_income,
                    :eps
                )
            """),
            {
                "period_id": period_id,
                "revenue": row["revenue"],
                "ebitda": row["ebitda"],
                "da": row["depreciation_amortization"],
                "ebit": row["ebit"],
                "finance_cost": row["finance_cost"],
                "pbt": row["profit_before_tax"],
                "tax_expense": row["tax_expense"],
                "net_income": row["net_income"],
                "eps": row["eps"],
            },
        )

        # ---------------- BALANCE SHEET ----------------

        conn.execute(
            text("""
                DELETE FROM fundamentals.balance_sheets
                WHERE period_id = :period_id
            """),
            {"period_id": period_id},
        )

        conn.execute(
            text("""
                INSERT INTO fundamentals.balance_sheets
                (
                    period_id,
                    cash_and_equivalents,
                    receivables,
                    current_assets,
                    property_plant_equipment,
                    total_assets,
                    payables,
                    current_liabilities,
                    total_debt,
                    total_liabilities,
                    shareholders_equity
                )
                VALUES
                (
                    :period_id,
                    :cash,
                    :receivables,
                    :current_assets,
                    :ppe,
                    :total_assets,
                    :payables,
                    :current_liabilities,
                    NULL,
                    :total_liabilities,
                    :shareholders_equity
                )
            """),
            {
                "period_id": period_id,
                "cash": row["cash"],
                "receivables": row["receivables"],
                "current_assets": row["current_assets"],
                "ppe": row["ppe"],
                "total_assets": row["total_assets"],
                "payables": row["payables"],
                "current_liabilities": row["current_liabilities"],
                "total_liabilities": row["total_liabilities"],
                "shareholders_equity": row["shareholders_equity"],
            },
        )

        # ---------------- CASH FLOW ----------------

        conn.execute(
            text("""
                DELETE FROM fundamentals.cash_flows
                WHERE period_id = :period_id
            """),
            {"period_id": period_id},
        )

        conn.execute(
            text("""
                INSERT INTO fundamentals.cash_flows
                (
                    period_id,
                    cash_from_operations,
                    capital_expenditure,
                    cash_from_investing,
                    cash_from_financing,
                    dividends_paid,
                    free_cash_flow
                )
                VALUES
                (
                    :period_id,
                    :cfo,
                    :capex,
                    :cfi,
                    :cff,
                    :dividends,
                    :fcf
                )
            """),
            {
                "period_id": period_id,
                "cfo": row["cfo"],
                "capex": row["capex"],
                "cfi": row["cfi"],
                "cff": row["cff"],
                "dividends": row["dividends_paid"],
                "fcf": row["free_cash_flow"],
            },
        )

        print(
            f"FY{fiscal_year} loaded "
            f"(period_id={period_id})"
        )

print("\nTransaction committed successfully.")
print("INFOSYS FY2022-FY2026 PostgreSQL load complete.")
