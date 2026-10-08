# FinSight 360 ? Methodology and Limitations

## Project Scope
FinSight 360 is a portfolio financial analytics project integrating
Python ETL, PostgreSQL, financial statement analysis, valuation,
portfolio research, FP&A, treasury analysis and reporting.

## Data Sources
Financial statement data is derived from company annual reports.
Market price data is processed separately.
Financial amounts, dates and units must be interpreted according
to the underlying source files.

## Valuation Assumptions
- DCF WACC of 12.25% is a modelling assumption, not an independently verified cost of capital.
- Terminal growth rates are scenario assumptions.
- Excess financial assets and lease liabilities require consistent treatment in the enterprise-to-equity bridge.
- FY2026 financial statements and the October 2026 market reference date are not the same valuation date.
- Historical free cash flow and forecast free cash flow to the firm are different measures.
- EV/EBITDA is omitted where standardized peer inputs are unavailable.

## Portfolio Risk
- Sharpe and Sortino calculations use a 0% risk-free baseline.
- Maximum-Sharpe optimization can create concentrated positions, particularly in HCLTECH.
- Historical backtests and stress scenarios do not guarantee future returns.

## Financial Statement Limitations
- Consolidated profit and parent-attributable profit must not be treated as interchangeable.
- Total equity and parent shareholders' equity may differ.
- Some HCLTECH financial statement fields remain unavailable in standardized datasets.
- HCLTECH FY2024 cash flow and depreciation fields were reconciled with the source report and PostgreSQL.

## Credit Scoring
The internal 98% credit score is a project-specific analytical output.
It is not a credit rating issued by a recognized rating agency.

## Reporting
The project uses an interactive HTML dashboard and Excel financial model.
Power BI is not required for the final deliverable.

## Disclaimer
This project is for educational and portfolio demonstration purposes.
It is not investment advice. Valuations and projections are estimates,
not guarantees or official company forecasts.
