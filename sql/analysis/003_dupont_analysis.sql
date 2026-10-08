CREATE OR REPLACE VIEW analytics.vw_dupont_analysis AS

WITH base AS (
    SELECT
        c.company_id,
        c.symbol,
        c.company_name,
        fp.fiscal_year,

        i.revenue,
        i.net_income,
        i.profit_attributable_to_owners,

        b.total_assets,
        b.equity_attributable_to_owners,

        LAG(b.total_assets) OVER (
            PARTITION BY c.company_id
            ORDER BY fp.fiscal_year
        ) AS previous_assets,

        LAG(b.equity_attributable_to_owners) OVER (
            PARTITION BY c.company_id
            ORDER BY fp.fiscal_year
        ) AS previous_owner_equity

    FROM fundamentals.financial_periods fp

    JOIN core.companies c
        ON c.company_id = fp.company_id

    LEFT JOIN fundamentals.income_statements i
        ON i.period_id = fp.period_id

    LEFT JOIN fundamentals.balance_sheets b
        ON b.period_id = fp.period_id

    WHERE fp.period_type = 'ANNUAL'
      AND fp.fiscal_year BETWEEN 2022 AND 2026
      AND c.symbol IN ('TCS', 'INFY', 'HCLTECH')
),

calc AS (
    SELECT
        *,

        (total_assets + previous_assets) / 2.0
            AS average_assets,

        (
            equity_attributable_to_owners +
            previous_owner_equity
        ) / 2.0 AS average_owner_equity

    FROM base
)

SELECT
    company_id,
    symbol,
    company_name,
    fiscal_year,

    revenue,

    -- Consolidated PAT retained for reference.
    net_income,

    -- DuPont shareholder return uses owner PAT.
    profit_attributable_to_owners,

    total_assets,
    equity_attributable_to_owners,

    ROUND(
        average_assets,
        2
    ) AS average_assets,

    ROUND(
        average_owner_equity,
        2
    ) AS average_owner_equity,

    ROUND(
        100.0 * profit_attributable_to_owners /
        NULLIF(revenue, 0),
        2
    ) AS owner_net_profit_margin_pct,

    ROUND(
        revenue /
        NULLIF(average_assets, 0),
        4
    ) AS asset_turnover,

    ROUND(
        average_assets /
        NULLIF(average_owner_equity, 0),
        4
    ) AS equity_multiplier,

    ROUND(
        100.0 *
        (
            profit_attributable_to_owners /
            NULLIF(revenue, 0)
        )
        *
        (
            revenue /
            NULLIF(average_assets, 0)
        )
        *
        (
            average_assets /
            NULLIF(average_owner_equity, 0)
        ),
        2
    ) AS dupont_roe_pct,

    ROUND(
        100.0 *
        profit_attributable_to_owners /
        NULLIF(average_owner_equity, 0),
        2
    ) AS direct_roe_pct

FROM calc;
