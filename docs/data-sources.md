# Data Sources

## Primary: iShares ETF Holdings

We fetch real holdings data from 8 iShares European ETFs:

| Ticker | Fund Name | Benchmark |
|--------|-----------|-----------|
| IMAE | iShares Core MSCI Europe | MSCI Europe |
| EUE | iShares EURO STOXX 50 | EURO STOXX 50 |
| SWDA | iShares Core MSCI World | MSCI World |
| EDMW | iShares MSCI Europe ESG Enhanced | MSCI Europe ESG Enhanced |
| IEAG | iShares Core EUR Aggregate Bond | Bloomberg Euro Aggregate |
| EXS1 | iShares Core DAX | DAX |
| IESE | iShares MSCI Europe SRI | MSCI Europe SRI |
| CSEMU | iShares Core MSCI EMU | MSCI EMU |

**Format**: CSV files downloaded from iShares website. The files have a quirky format with metadata header rows before the actual data table.

**Fields extracted**: Ticker, Name, ISIN, Weight (%), Sector, Asset Class, Country

## Enrichment: yfinance

Each asset ISIN is resolved to a yfinance ticker for enrichment:
- Sector and Industry (GICS classification)
- Market capitalization
- Country of domicile

Rate-limited to 0.5s between API calls with 7-day file-based caching.

## ESG: Kaggle Public Dataset

ESG scores from publicly available Kaggle datasets:
- Environment, Social, Governance sub-scores (0-10 scale)
- Total ESG score
- Risk level classification
- Controversy level (0-5)

**Manual download required** — place CSV in `data/raw/esg/` directory.

## Future: GLEIF LEI API

Corporate entity hierarchy data from the Global LEI Foundation:
- Legal Entity Identifier (LEI)
- Entity name and jurisdiction
- Parent-child corporate relationships

REST API, free access, no authentication required.
