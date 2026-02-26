"""Load validated domain models into Neo4j using batch MERGE operations.

Uses UNWIND for batch writes (much faster than individual MERGE statements).
All operations are idempotent via MERGE — safe to re-run.
"""

from __future__ import annotations

from loguru import logger

from amkg.graph.client import Neo4jClient
from amkg.models.nodes import Asset, Benchmark, Holding, Portfolio

# ============================================================
# BATCH MERGE QUERIES (UNWIND for performance)
# ============================================================

MERGE_PORTFOLIOS = """
UNWIND $batch AS row
MERGE (p:Portfolio {portfolio_id: row.portfolio_id})
SET p.name = row.name,
    p.isin = row.isin,
    p.asset_class = row.asset_class,
    p.currency = row.currency,
    p.aum = row.aum,
    p.morningstar_category = row.morningstar_category,
    p.morningstar_rating = row.morningstar_rating,
    p.domicile = row.domicile,
    p.is_active = row.is_active
"""

MERGE_BENCHMARKS = """
UNWIND $batch AS row
MERGE (b:Benchmark {benchmark_id: row.benchmark_id})
SET b.name = row.name,
    b.ticker = row.ticker,
    b.provider = row.provider,
    b.asset_class = row.asset_class,
    b.currency = row.currency,
    b.region = row.region
"""

MERGE_ASSETS = """
UNWIND $batch AS row
MERGE (a:Asset {isin: row.isin})
SET a.name = row.name,
    a.ticker = row.ticker,
    a.asset_type = row.asset_type,
    a.currency = row.currency,
    a.country = row.country,
    a.exchange = row.exchange,
    a.market_cap = row.market_cap,
    a.sector = row.sector,
    a.industry = row.industry
"""

MERGE_SECTORS = """
UNWIND $batch AS row
MERGE (s:Sector {sector_id: row.sector_id})
SET s.name = row.name,
    s.classification_system = row.classification_system,
    s.level = row.level
"""

MERGE_ENTITIES = """
UNWIND $batch AS row
MERGE (e:Entity {entity_id: row.entity_id})
SET e.name = row.name,
    e.entity_type = row.entity_type,
    e.country = row.country,
    e.parent_entity_id = row.parent_entity_id
"""

# ============================================================
# RELATIONSHIP MERGES
# ============================================================

MERGE_HOLDS = """
UNWIND $batch AS row
MATCH (p:Portfolio {portfolio_id: row.portfolio_id})
MATCH (a:Asset {isin: row.isin})
MERGE (p)-[r:HOLDS]->(a)
SET r.weight_pct = row.weight_pct,
    r.market_value = row.market_value,
    r.as_of_date = row.as_of_date
"""

MERGE_TRACKS = """
UNWIND $batch AS row
MATCH (p:Portfolio {portfolio_id: row.portfolio_id})
MATCH (b:Benchmark {benchmark_id: row.benchmark_id})
MERGE (p)-[r:TRACKS]->(b)
SET r.is_primary = true
"""

MERGE_BELONGS_TO = """
UNWIND $batch AS row
MATCH (a:Asset {isin: row.isin})
MATCH (s:Sector {name: row.sector_name})
MERGE (a)-[r:BELONGS_TO]->(s)
SET r.classification_system = 'GICS'
"""

MERGE_COMPOSED_OF = """
UNWIND $batch AS row
MATCH (b:Benchmark {benchmark_id: row.benchmark_id})
MATCH (a:Asset {isin: row.isin})
MERGE (b)-[r:COMPOSED_OF]->(a)
SET r.weight_pct = row.weight_pct,
    r.as_of_date = row.as_of_date
"""


class GraphLoader:
    """Load validated domain models into Neo4j."""

    def __init__(self, client: Neo4jClient) -> None:
        self.client = client

    def load_portfolios(self, portfolios: list[Portfolio]) -> int:
        """Batch merge portfolio nodes."""
        batch = [p.model_dump(mode="json") for p in portfolios]
        self.client.run_batch_write(MERGE_PORTFOLIOS, batch)
        logger.info(f"Loaded {len(batch)} portfolios")
        return len(batch)

    def load_benchmarks(self, benchmarks: list[Benchmark]) -> int:
        """Batch merge benchmark nodes."""
        batch = [b.model_dump(mode="json") for b in benchmarks]
        self.client.run_batch_write(MERGE_BENCHMARKS, batch)
        logger.info(f"Loaded {len(batch)} benchmarks")
        return len(batch)

    def load_assets(self, assets: list[Asset]) -> int:
        """Batch merge asset nodes (deduplicates by ISIN)."""
        seen: dict[str, Asset] = {}
        for a in assets:
            if a.isin not in seen:
                seen[a.isin] = a

        batch = [a.model_dump(mode="json") for a in seen.values()]
        self.client.run_batch_write(MERGE_ASSETS, batch)
        logger.info(f"Loaded {len(batch)} unique assets (from {len(assets)} total)")
        return len(batch)

    def load_sectors(self, sector_names: set[str]) -> int:
        """Create sector nodes from a set of sector names."""
        batch = [
            {
                "sector_id": f"GICS_{name.replace(' ', '_').upper()}",
                "name": name,
                "classification_system": "GICS",
                "level": 1,
            }
            for name in sector_names
            if name
        ]
        self.client.run_batch_write(MERGE_SECTORS, batch)
        logger.info(f"Loaded {len(batch)} sectors")
        return len(batch)

    def load_holdings(self, holdings: list[Holding]) -> int:
        """Create HOLDS relationships between portfolios and assets."""
        batch = [
            {
                "portfolio_id": h.portfolio_id,
                "isin": h.isin,
                "weight_pct": h.weight_pct,
                "market_value": h.market_value,
                "as_of_date": h.as_of_date.isoformat(),
            }
            for h in holdings
        ]
        self.client.run_batch_write(MERGE_HOLDS, batch)
        logger.info(f"Loaded {len(batch)} HOLDS relationships")
        return len(batch)

    def load_tracks(self, portfolio_benchmark_pairs: list[tuple[str, str]]) -> int:
        """Create TRACKS relationships between portfolios and benchmarks."""
        batch = [
            {"portfolio_id": pid, "benchmark_id": bid}
            for pid, bid in portfolio_benchmark_pairs
        ]
        self.client.run_batch_write(MERGE_TRACKS, batch)
        logger.info(f"Loaded {len(batch)} TRACKS relationships")
        return len(batch)

    def load_belongs_to(self, asset_sector_pairs: list[tuple[str, str]]) -> int:
        """Create BELONGS_TO relationships between assets and sectors."""
        batch = [
            {"isin": isin, "sector_name": sector}
            for isin, sector in asset_sector_pairs
            if sector
        ]
        self.client.run_batch_write(MERGE_BELONGS_TO, batch)
        logger.info(f"Loaded {len(batch)} BELONGS_TO relationships")
        return len(batch)

    def load_composed_of(
        self, benchmark_id: str, holdings: list[Holding]
    ) -> int:
        """Create COMPOSED_OF relationships (benchmark constituents)."""
        batch = [
            {
                "benchmark_id": benchmark_id,
                "isin": h.isin,
                "weight_pct": h.weight_pct,
                "as_of_date": h.as_of_date.isoformat(),
            }
            for h in holdings
        ]
        self.client.run_batch_write(MERGE_COMPOSED_OF, batch)
        logger.info(f"Loaded {len(batch)} COMPOSED_OF relationships for {benchmark_id}")
        return len(batch)

    def enrich_assets_from_yfinance(self, enrichments: dict[str, dict]) -> int:
        """Update asset nodes with yfinance data (sector, industry, market cap)."""
        batch = [
            {
                "ticker": ticker,
                "sector": data.get("sector", ""),
                "industry": data.get("industry", ""),
                "country": data.get("country", "")[:2] if data.get("country") else None,
                "exchange": data.get("exchange", ""),
                "market_cap": (data.get("market_cap", 0) or 0) / 1_000_000,  # to millions
            }
            for ticker, data in enrichments.items()
        ]
        query = """
        UNWIND $batch AS row
        MATCH (a:Asset {ticker: row.ticker})
        SET a.sector = CASE WHEN row.sector <> '' THEN row.sector ELSE a.sector END,
            a.industry = CASE WHEN row.industry <> '' THEN row.industry ELSE a.industry END,
            a.country = COALESCE(row.country, a.country),
            a.exchange = CASE WHEN row.exchange <> '' THEN row.exchange ELSE a.exchange END,
            a.market_cap = CASE WHEN row.market_cap > 0 THEN row.market_cap ELSE a.market_cap END
        """
        self.client.run_batch_write(query, batch)
        logger.info(f"Enriched {len(batch)} assets with yfinance data")
        return len(batch)
