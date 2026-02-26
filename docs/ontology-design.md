# Ontology Design

## Domain Model

The AMKG ontology models the European asset management domain with the following entity types and relationships.

## Node Types

### Portfolio
Represents an investment fund or ETF.
- `portfolio_id` (string, unique) — Fund ISIN or internal identifier
- `name` (string) — Fund name
- `asset_class` (enum) — Equity, FixedIncome, MultiAsset, etc.
- `aum` (float, >= 0) — Assets under management
- `morningstar_rating` (int, 1-5) — Star rating
- `benchmark_id` (string, nullable) — Tracked benchmark

### Benchmark
A market index that portfolios track.
- `benchmark_id` (string, unique)
- `name` (string)
- `provider` (string) — e.g., "MSCI", "STOXX"
- `asset_class` (enum)

### Asset
An individual security (equity, bond, etc.).
- `isin` (string, unique) — 12-character ISIN, regex-validated
- `name` (string)
- `asset_type` (enum) — Equity, Bond, Cash, etc.
- `country` (string, 2-char ISO) — Domicile
- `sector` (string, nullable)
- `industry` (string, nullable)
- `market_cap` (float, nullable)

### Sector
GICS industry classification hierarchy.
- `name` (string)
- `level` (int, 1-4) — GICS hierarchy level

### ESGRating
Environmental, Social, and Governance risk assessment.
- `environment_score` (float, 0-10)
- `social_score` (float, 0-10)
- `governance_score` (float, 0-10)
- `total_score` (float, 0-10)
- `risk_level` (enum) — Low, Medium, High, Severe, Negligible
- `controversy_level` (int, 0-5)

### Entity
Corporate entity with LEI identification.
- `lei` (string) — Legal Entity Identifier
- `name` (string)
- `jurisdiction` (string)

### FundManager
Individual or team managing a portfolio.
- `name` (string)
- `firm` (string)

## Relationship Types

| Relationship | Source | Target | Properties |
|-------------|--------|--------|------------|
| TRACKS | Portfolio | Benchmark | — |
| HOLDS | Portfolio | Asset | weight_pct, as_of_date |
| BELONGS_TO | Asset | Sector | — |
| HAS_PERFORMANCE | Portfolio | PerformanceRecord | — |
| MEASURED_AGAINST | PerformanceRecord | Benchmark | — |
| HAS_ESG_SCORE | Asset/Portfolio | ESGRating | — |
| RATED_BY | ESGRating | RatingProvider | — |
| MANAGED_BY | Portfolio | FundManager | since |
| WORKS_FOR | FundManager | Entity | — |
| COMPOSED_OF | Benchmark | Asset | weight_pct |
| PEER_OF | Portfolio | Portfolio | overlap_score |
| PARENT_OF | Entity | Entity | — |

## Competency Questions

The ontology is designed to answer:

1. Which assets are held across multiple portfolios? (cross-portfolio overlap)
2. What is the ESG risk exposure of a portfolio? (aggregated ESG scores)
3. Which sectors are overweighted relative to the benchmark?
4. What is the shortest path between two entities in the graph?
5. Which fund managers have the most similar investment styles?
6. What corporate entities have the most AUM under management?
7. Which portfolios have controversial ESG holdings?
8. How aligned is a portfolio with EU Taxonomy standards?
