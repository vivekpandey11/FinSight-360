CREATE OR REPLACE VIEW analytics.vw_daily_market_analytics AS

WITH prices AS (
    SELECT
        c.company_id,
        c.symbol,
        c.company_name,
        mp.trade_date,
        mp.adjusted_close AS price,

        LAG(mp.adjusted_close) OVER (
            PARTITION BY c.company_id
            ORDER BY mp.trade_date
        ) AS previous_price

    FROM market.market_prices mp

    JOIN core.companies c
        ON c.company_id = mp.company_id

    WHERE mp.adjusted_close IS NOT NULL
),

returns AS (
    SELECT
        *,

        CASE
            WHEN previous_price IS NOT NULL
             AND previous_price <> 0
            THEN price / previous_price - 1
        END AS daily_return

    FROM prices
),

analytics_calc AS (
    SELECT
        *,

        MAX(price) OVER (
            PARTITION BY company_id
            ORDER BY trade_date
            ROWS BETWEEN UNBOUNDED PRECEDING
            AND CURRENT ROW
        ) AS running_peak,

        STDDEV_SAMP(daily_return) OVER (
            PARTITION BY company_id
            ORDER BY trade_date
            ROWS BETWEEN 19 PRECEDING
            AND CURRENT ROW
        ) AS rolling_20d_daily_vol,

        STDDEV_SAMP(daily_return) OVER (
            PARTITION BY company_id
            ORDER BY trade_date
            ROWS BETWEEN 59 PRECEDING
            AND CURRENT ROW
        ) AS rolling_60d_daily_vol

    FROM returns
)

SELECT
    company_id,
    symbol,
    company_name,
    trade_date,

    ROUND(price::numeric, 4)
        AS adjusted_close,

    ROUND(
        (100.0 * daily_return)::numeric,
        4
    ) AS daily_return_pct,

    ROUND(
        (
            100.0 *
            (
                price /
                FIRST_VALUE(price) OVER (
                    PARTITION BY company_id
                    ORDER BY trade_date
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND UNBOUNDED FOLLOWING
                ) - 1
            )
        )::numeric,
        2
    ) AS cumulative_return_pct,

    ROUND(
        (
            100.0 *
            (
                price / NULLIF(running_peak, 0) - 1
            )
        )::numeric,
        2
    ) AS drawdown_pct,

    ROUND(
        (
            100.0 *
            rolling_20d_daily_vol *
            SQRT(252.0)
        )::numeric,
        2
    ) AS rolling_20d_volatility_pct,

    ROUND(
        (
            100.0 *
            rolling_60d_daily_vol *
            SQRT(252.0)
        )::numeric,
        2
    ) AS rolling_60d_volatility_pct

FROM analytics_calc;
