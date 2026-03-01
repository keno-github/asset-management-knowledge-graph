"""Load validated domain models into Neo4j using batch MERGE operations.

Uses UNWIND for batch writes (much faster than individual MERGE statements).
All operations are idempotent via MERGE — safe to re-run.

Every node and relationship carries lineage metadata:
  _source          — human-readable data source tag
  _ingested_at     — ISO 8601 timestamp of the pipeline run
  _pipeline_run_id — UUID identifying the pipeline execution
"""

from __future__ import annotations

from loguru import logger

from amkg.graph.client import Neo4jClient
from amkg.models.nodes import Asset, Benchmark, ESGRating, Holding, Portfolio

# ============================================================
# SKOS concept URI mapping for sector harmonization
# ============================================================

_SECTOR_SKOS_URI: dict[str, str] = {
    "Energy": "https://w3id.org/amkg/vocabulary/sectors#Energy",
    "Materials": "https://w3id.org/amkg/vocabulary/sectors#Materials",
    "Basic Materials": "https://w3id.org/amkg/vocabulary/sectors#Materials",
    "Industrials": "https://w3id.org/amkg/vocabulary/sectors#Industrials",
    "Consumer Discretionary": "https://w3id.org/amkg/vocabulary/sectors#ConsumerDiscretionary",
    "Consumer Cyclical": "https://w3id.org/amkg/vocabulary/sectors#ConsumerDiscretionary",
    "Consumer Staples": "https://w3id.org/amkg/vocabulary/sectors#ConsumerStaples",
    "Consumer Non-cyclical": "https://w3id.org/amkg/vocabulary/sectors#ConsumerStaples",
    "Consumer Defensive": "https://w3id.org/amkg/vocabulary/sectors#ConsumerStaples",
    "Health Care": "https://w3id.org/amkg/vocabulary/sectors#HealthCare",
    "Healthcare": "https://w3id.org/amkg/vocabulary/sectors#HealthCare",
    "Financials": "https://w3id.org/amkg/vocabulary/sectors#Financials",
    "Information Technology": "https://w3id.org/amkg/vocabulary/sectors#InformationTechnology",
    "Technology": "https://w3id.org/amkg/vocabulary/sectors#InformationTechnology",
    "Communication Services": "https://w3id.org/amkg/vocabulary/sectors#CommunicationServices",
    "Communication": "https://w3id.org/amkg/vocabulary/sectors#CommunicationServices",
    "Communications": "https://w3id.org/amkg/vocabulary/sectors#CommunicationServices",
    "Utilities": "https://w3id.org/amkg/vocabulary/sectors#Utilities",
    "Real Estate": "https://w3id.org/amkg/vocabulary/sectors#RealEstate",
}

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
    p.as_of_date = row.as_of_date,
    p.is_active = row.is_active,
    p._source = row._source,
    p._ingested_at = row._ingested_at,
    p._pipeline_run_id = row._pipeline_run_id
"""

MERGE_BENCHMARKS = """
UNWIND $batch AS row
MERGE (b:Benchmark {benchmark_id: row.benchmark_id})
SET b.name = row.name,
    b.ticker = row.ticker,
    b.provider = row.provider,
    b.asset_class = row.asset_class,
    b.currency = row.currency,
    b.region = row.region,
    b._source = row._source,
    b._ingested_at = row._ingested_at,
    b._pipeline_run_id = row._pipeline_run_id
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
    a.industry = row.industry,
    a._source = row._source,
    a._ingested_at = row._ingested_at,
    a._pipeline_run_id = row._pipeline_run_id
"""

MERGE_SECTORS = """
UNWIND $batch AS row
MERGE (s:Sector {sector_id: row.sector_id})
SET s.name = row.name,
    s.classification_system = row.classification_system,
    s.level = row.level,
    s.skos_concept_uri = row.skos_concept_uri,
    s._source = row._source,
    s._ingested_at = row._ingested_at,
    s._pipeline_run_id = row._pipeline_run_id
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
    r.as_of_date = row.as_of_date,
    r._source = row._source,
    r._ingested_at = row._ingested_at,
    r._pipeline_run_id = row._pipeline_run_id
"""

MERGE_TRACKS = """
UNWIND $batch AS row
MATCH (p:Portfolio {portfolio_id: row.portfolio_id})
MATCH (b:Benchmark {benchmark_id: row.benchmark_id})
MERGE (p)-[r:TRACKS]->(b)
SET r.is_primary = true,
    r._source = row._source,
    r._ingested_at = row._ingested_at,
    r._pipeline_run_id = row._pipeline_run_id
"""

MERGE_BELONGS_TO = """
UNWIND $batch AS row
MATCH (a:Asset {isin: row.isin})
MATCH (s:Sector {name: row.sector_name})
MERGE (a)-[r:BELONGS_TO]->(s)
SET r.classification_system = 'GICS',
    r._source = row._source,
    r._ingested_at = row._ingested_at,
    r._pipeline_run_id = row._pipeline_run_id
"""

MERGE_COMPOSED_OF = """
UNWIND $batch AS row
MATCH (b:Benchmark {benchmark_id: row.benchmark_id})
MATCH (a:Asset {isin: row.isin})
MERGE (b)-[r:COMPOSED_OF]->(a)
SET r.weight_pct = row.weight_pct,
    r.as_of_date = row.as_of_date,
    r._source = row._source,
    r._ingested_at = row._ingested_at,
    r._pipeline_run_id = row._pipeline_run_id
"""

MERGE_ESG_RATINGS = """
UNWIND $batch AS row
MERGE (esg:ESGRating {rating_id: row.rating_id})
SET esg.entity_id = row.entity_id,
    esg.overall_score = row.overall_score,
    esg.environmental_score = row.environmental_score,
    esg.social_score = row.social_score,
    esg.governance_score = row.governance_score,
    esg.risk_level = row.risk_level,
    esg.taxonomy_alignment_pct = row.taxonomy_alignment_pct,
    esg.controversy_score = row.controversy_score,
    esg.rating_date = row.rating_date,
    esg.provider = row.provider,
    esg._source = row._source,
    esg._ingested_at = row._ingested_at,
    esg._pipeline_run_id = row._pipeline_run_id
"""

MERGE_HAS_ESG_SCORE = """
UNWIND $batch AS row
MATCH (a:Asset {isin: row.isin})
MATCH (esg:ESGRating {rating_id: row.rating_id})
MERGE (a)-[r:HAS_ESG_SCORE]->(esg)
SET r.rating_date = row.rating_date,
    r._source = row._source,
    r._ingested_at = row._ingested_at,
    r._pipeline_run_id = row._pipeline_run_id
"""


class GraphLoader:
    """Load validated domain models into Neo4j."""

    def __init__(
        self,
        client: Neo4jClient,
        run_id: str = "",
        ingested_at: str = "",
    ) -> None:
        self.client = client
        self.run_id = run_id
        self.ingested_at = ingested_at

    def _lineage(self, source: str) -> dict:
        """Return lineage metadata dict to merge into batch rows."""
        return {
            "_source": source,
            "_ingested_at": self.ingested_at,
            "_pipeline_run_id": self.run_id,
        }

    def load_portfolios(self, portfolios: list[Portfolio]) -> int:
        """Batch merge portfolio nodes."""
        meta = self._lineage("iShares:ETF")
        batch = [{**p.model_dump(mode="json"), **meta} for p in portfolios]
        self.client.run_batch_write(MERGE_PORTFOLIOS, batch)
        logger.info(f"Loaded {len(batch)} portfolios")
        return len(batch)

    def load_benchmarks(self, benchmarks: list[Benchmark]) -> int:
        """Batch merge benchmark nodes."""
        meta = self._lineage("iShares:ETF")
        batch = [{**b.model_dump(mode="json"), **meta} for b in benchmarks]
        self.client.run_batch_write(MERGE_BENCHMARKS, batch)
        logger.info(f"Loaded {len(batch)} benchmarks")
        return len(batch)

    def load_assets(self, assets: list[Asset]) -> int:
        """Batch merge asset nodes (deduplicates by ISIN)."""
        seen: dict[str, Asset] = {}
        for a in assets:
            if a.isin not in seen:
                seen[a.isin] = a

        meta = self._lineage("iShares:ETF")
        batch = [{**a.model_dump(mode="json"), **meta} for a in seen.values()]
        self.client.run_batch_write(MERGE_ASSETS, batch)
        logger.info(f"Loaded {len(batch)} unique assets (from {len(assets)} total)")
        return len(batch)

    def load_sectors(self, sector_names: set[str]) -> int:
        """Create sector nodes from a set of sector names."""
        meta = self._lineage("iShares:GICS")
        batch = [
            {
                "sector_id": f"GICS_{name.replace(' ', '_').upper()}",
                "name": name,
                "classification_system": "GICS",
                "level": 1,
                "skos_concept_uri": _SECTOR_SKOS_URI.get(name),
                **meta,
            }
            for name in sector_names
            if name
        ]
        self.client.run_batch_write(MERGE_SECTORS, batch)
        logger.info(f"Loaded {len(batch)} sectors")
        return len(batch)

    def load_holdings(self, holdings: list[Holding]) -> int:
        """Create HOLDS relationships between portfolios and assets."""
        meta = self._lineage("iShares:ETF")
        batch = [
            {
                "portfolio_id": h.portfolio_id,
                "isin": h.isin,
                "weight_pct": h.weight_pct,
                "market_value": h.market_value,
                "as_of_date": h.as_of_date.isoformat(),
                **meta,
            }
            for h in holdings
        ]
        self.client.run_batch_write(MERGE_HOLDS, batch)
        logger.info(f"Loaded {len(batch)} HOLDS relationships")
        return len(batch)

    def load_tracks(self, portfolio_benchmark_pairs: list[tuple[str, str]]) -> int:
        """Create TRACKS relationships between portfolios and benchmarks."""
        meta = self._lineage("iShares:ETF")
        batch = [
            {"portfolio_id": pid, "benchmark_id": bid, **meta}
            for pid, bid in portfolio_benchmark_pairs
        ]
        self.client.run_batch_write(MERGE_TRACKS, batch)
        logger.info(f"Loaded {len(batch)} TRACKS relationships")
        return len(batch)

    def load_belongs_to(self, asset_sector_pairs: list[tuple[str, str]]) -> int:
        """Create BELONGS_TO relationships between assets and sectors."""
        meta = self._lineage("iShares:GICS")
        batch = [
            {"isin": isin, "sector_name": sector, **meta}
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
        meta = self._lineage("iShares:ETF")
        batch = [
            {
                "benchmark_id": benchmark_id,
                "isin": h.isin,
                "weight_pct": h.weight_pct,
                "as_of_date": h.as_of_date.isoformat(),
                **meta,
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
                "_ingested_at": self.ingested_at,
                "_pipeline_run_id": self.run_id,
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
            a.market_cap = CASE WHEN row.market_cap > 0 THEN row.market_cap ELSE a.market_cap END,
            a._source = CASE WHEN a._source IS NULL THEN 'yfinance' ELSE a._source + '+yfinance' END,
            a._ingested_at = row._ingested_at,
            a._pipeline_run_id = row._pipeline_run_id
        """
        self.client.run_batch_write(query, batch)
        logger.info(f"Enriched {len(batch)} assets with yfinance data")
        return len(batch)

    def load_esg_ratings(self, ratings: list[ESGRating]) -> int:
        """Batch merge ESGRating nodes."""
        batch = [
            {
                "rating_id": r.rating_id,
                "entity_id": r.entity_id,
                "overall_score": r.overall_score,
                "environmental_score": r.environmental_score,
                "social_score": r.social_score,
                "governance_score": r.governance_score,
                "risk_level": r.risk_level.value,
                "taxonomy_alignment_pct": r.taxonomy_alignment_pct,
                "controversy_score": r.controversy_score,
                "rating_date": r.rating_date.isoformat(),
                "provider": r.provider,
                "_source": r.provider,
                "_ingested_at": self.ingested_at,
                "_pipeline_run_id": self.run_id,
            }
            for r in ratings
        ]
        self.client.run_batch_write(MERGE_ESG_RATINGS, batch)
        logger.info(f"Loaded {len(batch)} ESG ratings")
        return len(batch)

    def load_has_esg_score(self, ratings: list[ESGRating]) -> int:
        """Create HAS_ESG_SCORE relationships between assets and ESG ratings."""
        batch = [
            {
                "isin": r.entity_id,
                "rating_id": r.rating_id,
                "rating_date": r.rating_date.isoformat(),
                "_source": r.provider,
                "_ingested_at": self.ingested_at,
                "_pipeline_run_id": self.run_id,
            }
            for r in ratings
        ]
        self.client.run_batch_write(MERGE_HAS_ESG_SCORE, batch)
        logger.info(f"Loaded {len(batch)} HAS_ESG_SCORE relationships")
        return len(batch)
