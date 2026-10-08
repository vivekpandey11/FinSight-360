CREATE OR REPLACE VIEW analytics.vw_peer_scorecard AS

WITH perf AS (
    SELECT *
    FROM analytics.vw_financial_performance
),

period_summary AS (
    SELECT
        symbol,
        company_name,

        MAX(CASE WHEN fiscal_year = 2022 THEN revenue END)
            AS revenue_fy22,

        MAX(CASE WHEN fiscal_year = 2026 THEN revenue END)
            AS revenue_fy26,

        MAX(
            CASE WHEN fiscal_year = 2022
            THEN profit_attributable_to_owners END
        ) AS owner_pat_fy22,

        MAX(
            CASE WHEN fiscal_year = 2026
            THEN profit_attributable_to_owners END
        ) AS owner_pat_fy26,

        MAX(CASE WHEN fiscal_year = 2022 THEN eps END)
            AS eps_fy22,

        MAX(CASE WHEN fiscal_year = 2026 THEN eps END)
            AS eps_fy26,

        MAX(CASE WHEN fiscal_year = 2022 THEN free_cash_flow END)
            AS fcf_fy22,

        MAX(CASE WHEN fiscal_year = 2026 THEN free_cash_flow END)
            AS fcf_fy26

    FROM perf

    GROUP BY
        symbol,
        company_name
),

latest AS (
    SELECT *
    FROM perf
    WHERE fiscal_year = 2026
),

metrics AS (
    SELECT
        l.symbol,
        l.company_name,

        l.revenue,

        -- Keep both definitions visible.
        l.net_income,
        l.profit_attributable_to_owners,

        l.eps,
        l.free_cash_flow,

        l.ebitda_margin_pct,
        l.net_profit_margin_pct,
        l.owner_pat_margin_pct,

        l.roe_pct,
        l.roa_pct,
        l.current_ratio,
        l.cfo_to_pat,
        l.fcf_conversion_pct,

        ROUND(
            100.0 *
            (
                POWER(
                    l.revenue /
                    NULLIF(p.revenue_fy22, 0),
                    1.0 / 4
                ) - 1
            ),
            2
        ) AS revenue_cagr_4y_pct,

        -- Shareholder earnings growth uses owner PAT.
        ROUND(
            100.0 *
            (
                POWER(
                    l.profit_attributable_to_owners /
                    NULLIF(p.owner_pat_fy22, 0),
                    1.0 / 4
                ) - 1
            ),
            2
        ) AS pat_cagr_4y_pct,

        ROUND(
            100.0 *
            (
                POWER(
                    l.eps /
                    NULLIF(p.eps_fy22, 0),
                    1.0 / 4
                ) - 1
            ),
            2
        ) AS eps_cagr_4y_pct,

        ROUND(
            100.0 *
            (
                POWER(
                    l.free_cash_flow /
                    NULLIF(p.fcf_fy22, 0),
                    1.0 / 4
                ) - 1
            ),
            2
        ) AS fcf_cagr_4y_pct

    FROM latest l

    JOIN period_summary p
        ON p.symbol = l.symbol
),

ranked AS (
    SELECT
        *,

        RANK() OVER (
            ORDER BY revenue_cagr_4y_pct DESC NULLS LAST
        ) AS revenue_growth_rank,

        RANK() OVER (
            ORDER BY pat_cagr_4y_pct DESC NULLS LAST
        ) AS pat_growth_rank,

        RANK() OVER (
            ORDER BY ebitda_margin_pct DESC NULLS LAST
        ) AS ebitda_margin_rank,

        -- Owner PAT margin makes shareholder-profit
        -- comparison consistent with PAT growth and ROE.
        RANK() OVER (
            ORDER BY owner_pat_margin_pct DESC NULLS LAST
        ) AS net_margin_rank,

        RANK() OVER (
            ORDER BY roe_pct DESC NULLS LAST
        ) AS roe_rank,

        RANK() OVER (
            ORDER BY roa_pct DESC NULLS LAST
        ) AS roa_rank,

        RANK() OVER (
            ORDER BY fcf_conversion_pct DESC NULLS LAST
        ) AS fcf_conversion_rank

    FROM metrics
)

SELECT
    *,

    (
        revenue_growth_rank +
        pat_growth_rank +
        ebitda_margin_rank +
        net_margin_rank +
        roe_rank +
        roa_rank +
        fcf_conversion_rank
    ) AS composite_rank_points,

    RANK() OVER (
        ORDER BY
        (
            revenue_growth_rank +
            pat_growth_rank +
            ebitda_margin_rank +
            net_margin_rank +
            roe_rank +
            roa_rank +
            fcf_conversion_rank
        ) ASC
    ) AS overall_peer_rank

FROM ranked;
