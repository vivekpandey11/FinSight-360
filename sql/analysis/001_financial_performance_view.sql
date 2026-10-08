CREATE OR REPLACE VIEW analytics.vw_financial_performance AS

WITH base AS (
    SELECT
        c.company_id,
        c.symbol,
        c.company_name,
        fp.fiscal_year,

        i.revenue,
        i.ebitda,
        i.ebit,
        i.profit_before_tax,

        -- Consolidated PAT retained for consolidated operating metrics.
        i.net_income,

        -- Parent/owner attributable PAT used for shareholder-return metrics.
        i.profit_attributable_to_owners,

        i.eps,

        b.cash_and_equivalents,
        b.receivables,
        b.current_assets,
        b.total_assets,
        b.current_liabilities,
        b.total_liabilities,

        -- Legacy field retained for lineage/backward compatibility.
        b.shareholders_equity,

        -- Standardized owner-attributable equity.
        b.equity_attributable_to_owners,
        b.non_controlling_interest,

        cf.cash_from_operations,
        cf.capital_expenditure,
        cf.cash_from_investing,
        cf.cash_from_financing,
        cf.dividends_paid,
        cf.free_cash_flow

    FROM fundamentals.financial_periods fp

    JOIN core.companies c
        ON c.company_id = fp.company_id

    LEFT JOIN fundamentals.income_statements i
        ON i.period_id = fp.period_id

    LEFT JOIN fundamentals.balance_sheets b
        ON b.period_id = fp.period_id

    LEFT JOIN fundamentals.cash_flows cf
        ON cf.period_id = fp.period_id

    WHERE fp.period_type = 'ANNUAL'
      AND fp.fiscal_year BETWEEN 2022 AND 2026
      AND c.symbol IN ('TCS', 'INFY', 'HCLTECH')
),

lagged AS (
    SELECT
        *,

        LAG(revenue) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_revenue,

        LAG(net_income) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_net_income,

        LAG(profit_attributable_to_owners) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_owner_pat,

        LAG(eps) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_eps,

        LAG(total_assets) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_total_assets,

        LAG(equity_attributable_to_owners) OVER (
            PARTITION BY company_id
            ORDER BY fiscal_year
        ) AS previous_owner_equity

    FROM base
)

SELECT
    company_id,
    symbol,
    company_name,
    fiscal_year,

    revenue,
    ebitda,
    ebit,
    profit_before_tax,

    net_income,
    profit_attributable_to_owners,
    eps,

    cash_and_equivalents,
    receivables,
    current_assets,
    total_assets,
    current_liabilities,
    total_liabilities,

    shareholders_equity,
    equity_attributable_to_owners,
    non_controlling_interest,

    cash_from_operations,
    capital_expenditure,
    cash_from_investing,
    cash_from_financing,
    dividends_paid,
    free_cash_flow,

    ROUND(
        100.0 * (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0),
        2
    ) AS revenue_yoy_pct,

    ROUND(
        100.0 * (net_income - previous_net_income)
        / NULLIF(previous_net_income, 0),
        2
    ) AS net_income_yoy_pct,

    ROUND(
        100.0 *
        (
            profit_attributable_to_owners -
            previous_owner_pat
        )
        / NULLIF(previous_owner_pat, 0),
        2
    ) AS owner_pat_yoy_pct,

    ROUND(
        100.0 * (eps - previous_eps)
        / NULLIF(previous_eps, 0),
        2
    ) AS eps_yoy_pct,

    ROUND(
        100.0 * ebitda
        / NULLIF(revenue, 0),
        2
    ) AS ebitda_margin_pct,

    ROUND(
        100.0 * ebit
        / NULLIF(revenue, 0),
        2
    ) AS ebit_margin_pct,

    -- Consolidated net margin.
    ROUND(
        100.0 * net_income
        / NULLIF(revenue, 0),
        2
    ) AS net_profit_margin_pct,

    -- Parent-shareholder earnings margin.
    ROUND(
        100.0 * profit_attributable_to_owners
        / NULLIF(revenue, 0),
        2
    ) AS owner_pat_margin_pct,

    ROUND(
        100.0 * free_cash_flow
        / NULLIF(revenue, 0),
        2
    ) AS fcf_margin_pct,

    ROUND(
        current_assets
        / NULLIF(current_liabilities, 0),
        2
    ) AS current_ratio,

    -- Shareholder leverage uses owner-attributable equity.
    ROUND(
        total_liabilities
        / NULLIF(equity_attributable_to_owners, 0),
        2
    ) AS liabilities_to_equity,

    -- ROE: owner PAT / average owner equity.
    ROUND(
        100.0 * profit_attributable_to_owners
        / NULLIF(
            (
                equity_attributable_to_owners +
                previous_owner_equity
            ) / 2.0,
            0
        ),
        2
    ) AS roe_pct,

    -- ROA remains consolidated PAT / average consolidated assets.
    ROUND(
        100.0 * net_income
        / NULLIF(
            (total_assets + previous_total_assets) / 2.0,
            0
        ),
        2
    ) AS roa_pct,

    -- CFO and consolidated PAT are both consolidated-group measures.
    ROUND(
        cash_from_operations
        / NULLIF(net_income, 0),
        2
    ) AS cfo_to_pat,

    ROUND(
        100.0 * free_cash_flow
        / NULLIF(cash_from_operations, 0),
        2
    ) AS fcf_conversion_pct

FROM lagged;
