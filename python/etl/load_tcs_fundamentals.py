from pathlib import Path

import pandas as pd
from sqlalchemy import text

from utils.db import get_engine


ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    ROOT
    / "data/interim/financials/TCS"
    / "TCS_fundamentals_FY2026_FY2025.csv"
)


def clean(value):
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


df = pd.read_csv(SOURCE)

required_years = {2025, 2026}

if set(df["fiscal_year"].astype(int)) != required_years:
    raise ValueError(
        f"Unexpected fiscal years: {df['fiscal_year'].tolist()}"
    )

if not (
    df[
        [
            "profit_valid",
            "balance_sheet_valid",
            "cash_flow_valid"
        ]
    ].all().all()
):
    raise ValueError("Source dataset contains failed validations.")


engine = get_engine()


with engine.begin() as conn:

    company_id = conn.execute(
        text("""
            SELECT company_id
            FROM core.companies
            WHERE symbol = 'TCS'
              AND asset_type = 'company'
        """)
    ).scalar_one()

    print(f"TCS company_id: {company_id}")

    for _, row in df.iterrows():

        fiscal_year = int(row["fiscal_year"])
        period_end = f"{fiscal_year}-03-31"

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
                    :period_end,
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
            {
                "company_id": company_id,
                "fiscal_year": fiscal_year,
                "period_end": period_end
            }
        ).scalar_one()

        values = {
            key: clean(value)
            for key, value in row.to_dict().items()
        }

        values["period_id"] = period_id

        # -------------------------
        # Income Statement
        # -------------------------

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
                    :depreciation_amortization,
                    :ebit,
                    :finance_cost,
                    :profit_before_tax,
                    :total_tax_expense,
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
            values
        )

        # -------------------------
        # Balance Sheet
        # -------------------------

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
                    :cash_and_equivalents,
                    :receivables,
                    :current_assets,
                    :property_plant_equipment,
                    :total_assets,
                    :trade_payables,
                    :current_liabilities,
                    NULL,
                    :total_liabilities,
                    :shareholders_equity
                )

                ON CONFLICT (period_id)

                DO UPDATE SET
                    cash_and_equivalents =
                        EXCLUDED.cash_and_equivalents,
                    receivables = EXCLUDED.receivables,
                    current_assets = EXCLUDED.current_assets,
                    property_plant_equipment =
                        EXCLUDED.property_plant_equipment,
                    total_assets = EXCLUDED.total_assets,
                    payables = EXCLUDED.payables,
                    current_liabilities =
                        EXCLUDED.current_liabilities,
                    total_debt = EXCLUDED.total_debt,
                    total_liabilities =
                        EXCLUDED.total_liabilities,
                    shareholders_equity =
                        EXCLUDED.shareholders_equity
            """),
            values
        )

        # -------------------------
        # Cash Flow
        # -------------------------

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
                    :cash_from_operations,
                    :capital_expenditure,
                    :cash_from_investing,
                    :cash_from_financing,
                    :dividends_paid,
                    :free_cash_flow
                )

                ON CONFLICT (period_id)

                DO UPDATE SET
                    cash_from_operations =
                        EXCLUDED.cash_from_operations,
                    capital_expenditure =
                        EXCLUDED.capital_expenditure,
                    cash_from_investing =
                        EXCLUDED.cash_from_investing,
                    cash_from_financing =
                        EXCLUDED.cash_from_financing,
                    dividends_paid =
                        EXCLUDED.dividends_paid,
                    free_cash_flow =
                        EXCLUDED.free_cash_flow
            """),
            values
        )

        print(
            f"FY{fiscal_year} loaded "
            f"(period_id={period_id})"
        )


print("\nFundamentals transaction committed successfully.")
