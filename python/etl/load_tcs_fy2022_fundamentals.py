from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

ROOT = Path.cwd()

SOURCE = (
    ROOT / "data" / "interim" / "financials" / "TCS" /
    "parsed_fundamentals_FY2023_FY2022.csv"
)

df = pd.read_csv(SOURCE)

# Only FY2022 is new.
row = df.loc[df["fiscal_year"] == 2022]

if len(row) != 1:
    raise ValueError("Expected exactly one FY2022 row.")

row = row.iloc[0]

# Convert NumPy/Pandas scalar values to native Python types
def pyval(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value

row = row.map(pyval)

engine = get_engine()

with engine.begin() as conn:

    company_id = conn.execute(
        text("""
            SELECT company_id
            FROM core.companies
            WHERE symbol = 'TCS'
        """)
    ).scalar_one()

    print(f"TCS company_id: {company_id}")

    # Financial period
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
                    2022,
                    'ANNUAL',
                    '2022-03-31',
                    'INR',
                    'INR_CRORE'
                )
            ON CONFLICT
                (company_id, period_type, period_end_date)
            DO UPDATE SET
                fiscal_year = EXCLUDED.fiscal_year,
                currency = EXCLUDED.currency,
                unit_scale = EXCLUDED.unit_scale
            RETURNING period_id
        """),
        {"company_id": company_id}
    ).scalar_one()

    # Income statement
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
            ON CONFLICT (period_id)
            DO UPDATE SET
                revenue = EXCLUDED.revenue,
                operating_expenses = EXCLUDED.operating_expenses,
                ebitda = EXCLUDED.ebitda,
                depreciation_amortization =
                    EXCLUDED.depreciation_amortization,
                ebit = EXCLUDED.ebit,
                finance_cost = EXCLUDED.finance_cost,
                profit_before_tax = EXCLUDED.profit_before_tax,
                tax_expense = EXCLUDED.tax_expense,
                net_income = EXCLUDED.net_income,
                eps = EXCLUDED.eps
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
        }
    )

    # Balance sheet
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
            ON CONFLICT (period_id)
            DO UPDATE SET
                cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                receivables = EXCLUDED.receivables,
                current_assets = EXCLUDED.current_assets,
                property_plant_equipment =
                    EXCLUDED.property_plant_equipment,
                total_assets = EXCLUDED.total_assets,
                payables = EXCLUDED.payables,
                current_liabilities = EXCLUDED.current_liabilities,
                total_debt = EXCLUDED.total_debt,
                total_liabilities = EXCLUDED.total_liabilities,
                shareholders_equity = EXCLUDED.shareholders_equity
        """),
        {
            "period_id": period_id,
            "cash": row["cash_and_equivalents"],
            "receivables": row["receivables"],
            "current_assets": row["current_assets"],
            "ppe": row["property_plant_equipment"],
            "total_assets": row["total_assets"],
            "payables": row["payables"],
            "current_liabilities": row["current_liabilities"],
            "total_liabilities": row["total_liabilities"],
            "shareholders_equity": row["shareholders_equity"],
        }
    )

    # Cash flow
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
            ON CONFLICT (period_id)
            DO UPDATE SET
                cash_from_operations = EXCLUDED.cash_from_operations,
                capital_expenditure = EXCLUDED.capital_expenditure,
                cash_from_investing = EXCLUDED.cash_from_investing,
                cash_from_financing = EXCLUDED.cash_from_financing,
                dividends_paid = EXCLUDED.dividends_paid,
                free_cash_flow = EXCLUDED.free_cash_flow
        """),
        {
            "period_id": period_id,
            "cfo": row["cash_from_operations"],
            "capex": row["capital_expenditure"],
            "cfi": row["cash_from_investing"],
            "cff": row["cash_from_financing"],
            "dividends": row["dividends_paid"],
            "fcf": row["free_cash_flow"],
        }
    )

    print(f"FY2022 loaded successfully (period_id={period_id})")

print("\nTransaction committed successfully.")
print("TCS FY2022 PostgreSQL load complete.")
