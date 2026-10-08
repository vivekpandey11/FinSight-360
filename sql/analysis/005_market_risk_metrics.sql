CREATE OR REPLACE VIEW analytics.vw_market_risk_metrics AS

WITH daily AS (
    SELECT
        symbol,
        trade_date,
        adjusted_close,
        daily_return_pct / 100.0 AS daily_return
    FROM analytics.vw_daily_market_analytics
    WHERE daily_return_pct IS NOT NULL
),

asset_summary AS (
    SELECT
        symbol,
        COUNT(*) AS return_observations,

        AVG(daily_return) AS avg_daily_return,

        STDDEV_SAMP(daily_return) AS daily_volatility

    FROM daily
    GROUP BY symbol
),

paired AS (
    SELECT
        a.symbol,
        a.trade_date,
        a.daily_return AS asset_return,
        b.daily_return AS benchmark_return

    FROM daily a

    JOIN daily b
        ON a.trade_date = b.trade_date
       AND b.symbol = 'NIFTY50'

    WHERE a.symbol <> 'NIFTY50'
),

benchmark_stats AS (
    SELECT
        AVG(daily_return) AS benchmark_avg_daily_return,
        VAR_SAMP(daily_return) AS benchmark_variance
    FROM daily
    WHERE symbol = 'NIFTY50'
),

relative_metrics AS (
    SELECT
        symbol,

        COUNT(*) AS paired_observations,

        COVAR_SAMP(
            asset_return,
            benchmark_return
        )
        /
        NULLIF(
            VAR_SAMP(benchmark_return),
            0
        ) AS beta,

        CORR(
            asset_return,
            benchmark_return
        ) AS correlation,

        AVG(asset_return) AS paired_asset_avg_return,

        AVG(benchmark_return) AS paired_benchmark_avg_return

    FROM paired
    GROUP BY symbol
),

combined AS (
    SELECT
        s.symbol,
        s.return_observations,

        s.avg_daily_return,
        s.daily_volatility,

        CASE
            WHEN s.symbol = 'NIFTY50'
            THEN 1.0
            ELSE r.beta
        END AS beta,

        CASE
            WHEN s.symbol = 'NIFTY50'
            THEN 1.0
            ELSE r.correlation
        END AS correlation,

        CASE
            WHEN s.symbol = 'NIFTY50'
            THEN NULL
            ELSE
                (
                    r.paired_asset_avg_return
                    -
                    (
                        r.beta *
                        r.paired_benchmark_avg_return
                    )
                ) * 252
        END AS annualized_alpha,

        CASE
            WHEN s.symbol = 'NIFTY50'
            THEN s.return_observations
            ELSE r.paired_observations
        END AS paired_observations

    FROM asset_summary s

    LEFT JOIN relative_metrics r
        ON r.symbol = s.symbol

    CROSS JOIN benchmark_stats b
)

SELECT
    symbol,
    return_observations,
    paired_observations,

    ROUND(
        (
            100.0 *
            (
                POWER(
                    1.0 + avg_daily_return,
                    252.0
                ) - 1.0
            )
        )::numeric,
        2
    ) AS annualized_return_pct,

    ROUND(
        (
            100.0 *
            daily_volatility *
            SQRT(252.0)
        )::numeric,
        2
    ) AS annualized_volatility_pct,

    ROUND(
        beta::numeric,
        4
    ) AS beta_vs_nifty50,

    ROUND(
        correlation::numeric,
        4
    ) AS correlation_vs_nifty50,

    ROUND(
        (
            100.0 * annualized_alpha
        )::numeric,
        2
    ) AS annualized_alpha_pct,

    ROUND(
        (
            (
                avg_daily_return /
                NULLIF(daily_volatility, 0)
            )
            * SQRT(252.0)
        )::numeric,
        4
    ) AS sharpe_zero_rf

FROM combined;
