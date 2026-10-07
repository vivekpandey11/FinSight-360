from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db import get_engine

CSV = Path(
    "data/interim/financials/HCLTECH/"
    "HCLTECH_fundamentals_FY2022_FY2026.csv"
)

df = pd.read_csv(CSV)

def clean(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v

engine = get_engine()

with engine.begin() as conn:

    company_id = conn.execute(
        text("""
            SELECT company_id
            FROM core.companies
            WHERE symbol = 'HCLTECH'
            LIMIT 1
        """)
    ).scalar()

    if company_id is None:
        raise ValueError("HCLTECH not found in core.companies")

    print(f"HCLTECH company_id: {company_id}")

    for _, raw in df.iterrows():

        r = {k: clean(v) for k, v in raw.items()}
        fy = int(r["fiscal_year"])

        period_id = conn.execute(
            text("""
                SELECT period_id
                FROM fundamentals.financial_periods
                WHERE company_id = :company_id
                  AND fiscal_year = :fy
                  AND period_type = 'ANNUAL'
                LIMIT 1
            """),
            {
                "company_id": company_id,
                "fy": fy
            }
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
                        :fy,
                        'ANNUAL',
                        :period_end,
                        'INR',
                        'CRORE'
                    )
                    RETURNING period_id
                """),
                {
                    "company_id": company_id,
                    "fy": fy,
                    "period_end": f"{fy}-03-31"
                }
            ).scalar()

        # ---------- Income Statement ----------

        conn.execute(
            text("""
                DELETE FROM fundamentals.income_statements
                WHERE period_id = :pid
            """),
            {"pid": period_id}
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
                    :pid,
                    :revenue,
                    NULL,
                    :ebitda,
                    :da,
                    :ebit,
                    :finance,
                    :pbt,
                    :tax,
                    :pat,
                    :eps
                )
            """),
            {
                "pid": period_id,
                "revenue": r["revenue"],
                "ebitda": r["ebitda"],
                "da": r["depreciation_amortization"],
                "ebit": r["ebit"],
                "finance": r["finance_cost"],
                "pbt": r["profit_before_tax"],
                "tax": r["tax_expense"],
                "pat": r["net_income"],
                "eps": r["eps"]
            }
        )

        # ---------- Balance Sheet ----------

        conn.execute(
            text("""
                DELETE FROM fundamentals.balance_sheets
                WHERE period_id = :pid
            """),
            {"pid": period_id}
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
                    :pid,
                    :cash,
                    NULL,
                    :current_assets,
                    NULL,
                    :assets,
                    NULL,
                    :current_liabilities,
                    NULL,
                    :liabilities,
                    :equity
                )
            """),
            {
                "pid": period_id,
                "cash": r["cash_and_equivalents"],
                "current_assets": r["current_assets"],
                "assets": r["total_assets"],
                "current_liabilities": r["current_liabilities"],
                "liabilities": r["total_liabilities"],
                "equity": r["total_equity"]
            }
        )

        # ---------- Cash Flow ----------

        conn.execute(
            text("""
                DELETE FROM fundamentals.cash_flows
                WHERE period_id = :pid
            """),
            {"pid": period_id}
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
                    :pid,
                    :cfo,
                    :capex,
                    :cfi,
                    :cff,
                    :dividend,
                    :fcf
                )
            """),
            {
                "pid": period_id,
                "cfo": r["operating_cash_flow"],
                "capex": r["capital_expenditure"],
                "cfi": r["investing_cash_flow"],
                "cff": r["financing_cash_flow"],
                "dividend": r["dividends_paid"],
                "fcf": r["free_cash_flow"]
            }
        )

        print(
            f"FY{fy} loaded "
            f"(period_id={period_id})"
        )

print("\nTransaction committed successfully.")
print("HCLTECH FY2022-FY2026 PostgreSQL load complete.")
