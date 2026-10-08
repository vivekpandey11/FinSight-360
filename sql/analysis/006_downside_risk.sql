CREATE OR REPLACE VIEW analytics.vw_downside_risk AS

WITH returns AS (
    SELECT
        symbol,
        trade_date,
        daily_return_pct / 100.0 AS daily_return
    FROM analytics.vw_daily_market_analytics
    WHERE daily_return_pct IS NOT NULL
),

stats AS (
    SELECT
        symbol,

        COUNT(*) AS observations,

        AVG(daily_return) AS avg_daily_return,

        STDDEV_SAMP(
            CASE
                WHEN daily_return < 0
                THEN daily_return
            END
        ) AS downside_deviation,

        PERCENTILE_CONT(0.05)
        WITHIN GROUP (
            ORDER BY daily_return
        ) AS var_95_daily

    FROM returns

    GROUP BY symbol
),

cvar AS (
    SELECT
        r.symbol,

        AVG(r.daily_return)
            AS cvar_95_daily

    FROM returns r

    JOIN stats s
        ON s.symbol = r.symbol

    WHERE r.daily_return
          <= s.var_95_daily

    GROUP BY r.symbol
)

SELECT
    s.symbol,
    s.observations,

    ROUND(
        (
            100.0 *
            s.downside_deviation *
            SQRT(252.0)
        )::numeric,
        2
    ) AS annualized_downside_deviation_pct,

    ROUND(
        (
            (
                s.avg_daily_return /
                NULLIF(
                    s.downside_deviation,
                    0
                )
            )
            * SQRT(252.0)
        )::numeric,
        4
    ) AS sortino_zero_rf,

    ROUND(
        (
            100.0 *
            s.var_95_daily
        )::numeric,
        4
    ) AS historical_var_95_daily_pct,

    ROUND(
        (
            100.0 *
            c.cvar_95_daily
        )::numeric,
        4
    ) AS historical_cvar_95_daily_pct

FROM stats s

JOIN cvar c
    ON c.symbol = s.symbol;
