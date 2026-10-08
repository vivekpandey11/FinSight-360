CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS market;
CREATE SCHEMA IF NOT EXISTS fundamentals;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS research;

CREATE TABLE IF NOT EXISTS core.companies (
    company_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    ticker VARCHAR(30) UNIQUE NOT NULL,
    asset_type VARCHAR(30) NOT NULL
        CHECK (asset_type IN ('company', 'benchmark')),
    sector VARCHAR(100),
    industry VARCHAR(100),
    currency VARCHAR(10) DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market.market_prices (
    price_id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL
        REFERENCES core.companies(company_id),
    trade_date DATE NOT NULL,
    open_price NUMERIC(18,4),
    high_price NUMERIC(18,4),
    low_price NUMERIC(18,4),
    close_price NUMERIC(18,4) NOT NULL,
    adjusted_close NUMERIC(18,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_market_company_date
        UNIQUE(company_id, trade_date),

    CONSTRAINT chk_positive_close
        CHECK(close_price > 0),

    CONSTRAINT chk_nonnegative_volume
        CHECK(volume IS NULL OR volume >= 0),

    CONSTRAINT chk_high_price
        CHECK(
            high_price IS NULL OR
            (
                high_price >= open_price
                AND high_price >= low_price
                AND high_price >= close_price
            )
        ),

    CONSTRAINT chk_low_price
        CHECK(
            low_price IS NULL OR
            (
                low_price <= open_price
                AND low_price <= high_price
                AND low_price <= close_price
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_market_prices_date
ON market.market_prices(trade_date);

CREATE INDEX IF NOT EXISTS idx_market_prices_company
ON market.market_prices(company_id);

CREATE INDEX IF NOT EXISTS idx_market_prices_company_date
ON market.market_prices(company_id, trade_date);


CREATE TABLE IF NOT EXISTS fundamentals.financial_periods (
    period_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL
        REFERENCES core.companies(company_id),
    fiscal_year INTEGER NOT NULL,
    period_type VARCHAR(20) NOT NULL
        CHECK(period_type IN ('ANNUAL', 'QUARTERLY')),
    period_end_date DATE NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    unit_scale VARCHAR(20) DEFAULT 'INR_CRORE',

    CONSTRAINT uq_financial_period
        UNIQUE(company_id, period_type, period_end_date)
);


CREATE TABLE IF NOT EXISTS fundamentals.income_statements (
    income_statement_id BIGSERIAL PRIMARY KEY,
    period_id INTEGER UNIQUE NOT NULL
        REFERENCES fundamentals.financial_periods(period_id),
    revenue NUMERIC(20,2),
    operating_expenses NUMERIC(20,2),
    ebitda NUMERIC(20,2),
    depreciation_amortization NUMERIC(20,2),
    ebit NUMERIC(20,2),
    finance_cost NUMERIC(20,2),
    profit_before_tax NUMERIC(20,2),
    tax_expense NUMERIC(20,2),
    net_income NUMERIC(20,2),
    profit_attributable_to_owners NUMERIC(20,2),
    eps NUMERIC(18,4)
);


CREATE TABLE IF NOT EXISTS fundamentals.balance_sheets (
    balance_sheet_id BIGSERIAL PRIMARY KEY,
    period_id INTEGER UNIQUE NOT NULL
        REFERENCES fundamentals.financial_periods(period_id),
    cash_and_equivalents NUMERIC(20,2),
    receivables NUMERIC(20,2),
    current_assets NUMERIC(20,2),
    property_plant_equipment NUMERIC(20,2),
    total_assets NUMERIC(20,2),
    payables NUMERIC(20,2),
    current_liabilities NUMERIC(20,2),
    total_debt NUMERIC(20,2),
    total_liabilities NUMERIC(20,2),
    shareholders_equity NUMERIC(20,2),
    equity_attributable_to_owners NUMERIC(20,2),
    non_controlling_interest NUMERIC(20,2)
);


CREATE TABLE IF NOT EXISTS fundamentals.cash_flows (
    cash_flow_id BIGSERIAL PRIMARY KEY,
    period_id INTEGER UNIQUE NOT NULL
        REFERENCES fundamentals.financial_periods(period_id),
    cash_from_operations NUMERIC(20,2),
    capital_expenditure NUMERIC(20,2),
    cash_from_investing NUMERIC(20,2),
    cash_from_financing NUMERIC(20,2),
    dividends_paid NUMERIC(20,2),
    free_cash_flow NUMERIC(20,2)
);


CREATE TABLE IF NOT EXISTS analytics.financial_ratios (
    ratio_id BIGSERIAL PRIMARY KEY,
    period_id INTEGER UNIQUE NOT NULL
        REFERENCES fundamentals.financial_periods(period_id),
    revenue_growth NUMERIC(12,6),
    ebitda_margin NUMERIC(12,6),
    net_margin NUMERIC(12,6),
    roe NUMERIC(12,6),
    roa NUMERIC(12,6),
    roce NUMERIC(12,6),
    current_ratio NUMERIC(12,6),
    debt_to_equity NUMERIC(12,6),
    interest_coverage NUMERIC(12,6),
    asset_turnover NUMERIC(12,6),
    cfo_to_pat NUMERIC(12,6),
    fcf_margin NUMERIC(12,6)
);


CREATE TABLE IF NOT EXISTS research.macro_indicators (
    macro_id BIGSERIAL PRIMARY KEY,
    observation_date DATE NOT NULL,
    indicator VARCHAR(100) NOT NULL,
    value NUMERIC(20,6),
    unit VARCHAR(50),
    source VARCHAR(200),

    CONSTRAINT uq_macro_observation
        UNIQUE(observation_date, indicator)
);


CREATE TABLE IF NOT EXISTS research.valuation_assumptions (
    assumption_id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL
        REFERENCES core.companies(company_id),
    valuation_date DATE NOT NULL,
    scenario VARCHAR(20) NOT NULL
        CHECK(scenario IN ('BEAR', 'BASE', 'BULL')),
    risk_free_rate NUMERIC(12,6),
    equity_risk_premium NUMERIC(12,6),
    beta NUMERIC(12,6),
    cost_of_equity NUMERIC(12,6),
    cost_of_debt NUMERIC(12,6),
    tax_rate NUMERIC(12,6),
    wacc NUMERIC(12,6),
    terminal_growth_rate NUMERIC(12,6),

    CONSTRAINT uq_valuation_assumption
        UNIQUE(company_id, valuation_date, scenario)
);


CREATE TABLE IF NOT EXISTS analytics.valuation_results (
    valuation_id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL
        REFERENCES core.companies(company_id),
    valuation_date DATE NOT NULL,
    scenario VARCHAR(20) NOT NULL
        CHECK(scenario IN ('BEAR', 'BASE', 'BULL')),
    enterprise_value NUMERIC(24,2),
    equity_value NUMERIC(24,2),
    intrinsic_value_per_share NUMERIC(18,4),
    market_price NUMERIC(18,4),
    upside_downside_pct NUMERIC(12,6),

    CONSTRAINT uq_valuation_result
        UNIQUE(company_id, valuation_date, scenario)
);

