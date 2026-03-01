"""Load entities extracted from documents into Neo4j.

Reuses the same MERGE queries from the main pipeline loader to ensure
consistent graph structure and provenance metadata.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from loguru import logger

from amkg.graph.client import Neo4jClient
from amkg.pipeline.document_extractor import ExtractionResult
from amkg.pipeline.loader import (
    _SECTOR_SKOS_URI,
    MERGE_ASSETS,
    MERGE_BELONGS_TO,
    MERGE_BENCHMARKS,
    MERGE_HOLDS,
    MERGE_PORTFOLIOS,
    MERGE_SECTORS,
    MERGE_TRACKS,
)


class DocumentIngestionStats:
    """Track what was written to Neo4j during document ingestion."""

    def __init__(self) -> None:
        self.portfolios: int = 0
        self.assets: int = 0
        self.sectors: int = 0
        self.benchmarks: int = 0
        self.holds_relationships: int = 0
        self.belongs_to_relationships: int = 0
        self.tracks_relationships: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "portfolios": self.portfolios,
            "assets": self.assets,
            "sectors": self.sectors,
            "benchmarks": self.benchmarks,
            "holds_relationships": self.holds_relationships,
            "belongs_to_relationships": self.belongs_to_relationships,
            "tracks_relationships": self.tracks_relationships,
        }


def _generate_portfolio_id(portfolio: dict) -> str:
    """Generate a stable portfolio_id from available identifiers."""
    if portfolio.get("ticker"):
        return f"DOC_{portfolio['ticker'].upper()}"
    if portfolio.get("isin"):
        return f"DOC_{portfolio['isin']}"
    # Fallback: slugify the name
    name = portfolio.get("name", "UNKNOWN")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    return f"DOC_{slug}"


def _generate_isin(holding: dict) -> str:
    """Generate a synthetic ISIN for holdings without one.

    Format: XX + first 10 chars of uppercased name (padded with zeros).
    This ensures assets can still be merged by ISIN.
    """
    if holding.get("isin") and len(holding["isin"]) == 12:
        return holding["isin"]

    name = holding.get("asset_name", holding.get("ticker", "UNKNOWN"))
    slug = re.sub(r"[^A-Za-z0-9]", "", name).upper()[:10]
    return f"XX{slug.ljust(10, '0')}"


def load_extraction_to_neo4j(
    client: Neo4jClient,
    extraction: ExtractionResult,
) -> DocumentIngestionStats:
    """Write extracted entities and relationships to Neo4j.

    Args:
        client: Active Neo4j client.
        extraction: Validated extraction result from Claude.

    Returns:
        Stats on what was written.
    """
    stats = DocumentIngestionStats()
    run_id = str(uuid.uuid4())
    ingested_at = datetime.now(timezone.utc).isoformat()
    source = "document_extraction"

    lineage = {
        "_source": source,
        "_ingested_at": ingested_at,
        "_pipeline_run_id": run_id,
    }

    # Build portfolio_id lookup: portfolio_name -> portfolio_id
    portfolio_id_map: dict[str, str] = {}

    # --- Portfolios ---
    if extraction.portfolios:
        portfolio_batch: list[dict] = []
        for p in extraction.portfolios:
            row = p.model_dump(mode="json")
            pid = _generate_portfolio_id(row)
            portfolio_id_map[p.name] = pid
            portfolio_batch.append({
                "portfolio_id": pid,
                "name": p.name,
                "isin": p.isin,
                "asset_class": p.asset_class,
                "currency": p.currency,
                "aum": p.aum,
                "morningstar_category": None,
                "morningstar_rating": None,
                "domicile": p.domicile,
                "as_of_date": None,
                "is_active": True,
                **lineage,
            })
        client.run_batch_write(MERGE_PORTFOLIOS, portfolio_batch)
        stats.portfolios = len(portfolio_batch)
        logger.info(f"[DocIngest] Wrote {stats.portfolios} portfolios")

    # --- Assets (from holdings) ---
    if extraction.holdings:
        seen_isins: set[str] = set()
        asset_batch: list[dict] = []
        for h in extraction.holdings:
            isin = _generate_isin(h.model_dump(mode="json"))
            if isin in seen_isins:
                continue
            seen_isins.add(isin)
            asset_batch.append({
                "isin": isin,
                "name": h.asset_name,
                "ticker": h.ticker,
                "asset_type": None,
                "currency": None,
                "country": h.country,
                "exchange": None,
                "market_cap": None,
                "sector": h.sector,
                "industry": None,
                **lineage,
            })
        client.run_batch_write(MERGE_ASSETS, asset_batch)
        stats.assets = len(asset_batch)
        logger.info(f"[DocIngest] Wrote {stats.assets} assets")

    # --- Sectors ---
    sector_names: set[str] = set()
    for h in extraction.holdings:
        if h.sector:
            sector_names.add(h.sector)

    if sector_names:
        sector_batch: list[dict] = []
        for name in sector_names:
            sector_batch.append({
                "sector_id": f"GICS_{name.replace(' ', '_').upper()}",
                "name": name,
                "classification_system": "GICS",
                "level": 1,
                "skos_concept_uri": _SECTOR_SKOS_URI.get(name),
                **lineage,
            })
        client.run_batch_write(MERGE_SECTORS, sector_batch)
        stats.sectors = len(sector_batch)
        logger.info(f"[DocIngest] Wrote {stats.sectors} sectors")

    # --- Benchmarks ---
    if extraction.benchmarks:
        benchmark_batch: list[dict] = []
        for b in extraction.benchmarks:
            bid = f"DOC_{re.sub(r'[^A-Za-z0-9]+', '_', b.name).strip('_').upper()}"
            benchmark_batch.append({
                "benchmark_id": bid,
                "name": b.name,
                "ticker": b.ticker,
                "provider": b.provider,
                "asset_class": b.asset_class,
                "currency": None,
                "region": None,
                **lineage,
            })
        client.run_batch_write(MERGE_BENCHMARKS, benchmark_batch)
        stats.benchmarks = len(benchmark_batch)
        logger.info(f"[DocIngest] Wrote {stats.benchmarks} benchmarks")

    # --- HOLDS relationships ---
    if extraction.holdings:
        holds_batch: list[dict] = []
        for h in extraction.holdings:
            pid = portfolio_id_map.get(h.portfolio_name)
            if not pid:
                continue
            isin = _generate_isin(h.model_dump(mode="json"))
            holds_batch.append({
                "portfolio_id": pid,
                "isin": isin,
                "weight_pct": h.weight_pct,
                "market_value": None,
                "as_of_date": ingested_at[:10],
                **lineage,
            })
        client.run_batch_write(MERGE_HOLDS, holds_batch)
        stats.holds_relationships = len(holds_batch)
        logger.info(f"[DocIngest] Wrote {stats.holds_relationships} HOLDS relationships")

    # --- BELONGS_TO relationships ---
    if extraction.holdings:
        belongs_batch: list[dict] = []
        for h in extraction.holdings:
            if not h.sector:
                continue
            isin = _generate_isin(h.model_dump(mode="json"))
            belongs_batch.append({
                "isin": isin,
                "sector_name": h.sector,
                **lineage,
            })
        client.run_batch_write(MERGE_BELONGS_TO, belongs_batch)
        stats.belongs_to_relationships = len(belongs_batch)
        logger.info(
            f"[DocIngest] Wrote {stats.belongs_to_relationships} BELONGS_TO relationships"
        )

    # --- TRACKS relationships ---
    if extraction.benchmarks and extraction.portfolios:
        tracks_batch: list[dict] = []
        # If there's exactly one portfolio and one+ benchmarks, link them
        if len(extraction.portfolios) == 1:
            pid = portfolio_id_map.get(extraction.portfolios[0].name)
            if pid:
                for b in extraction.benchmarks:
                    bid = f"DOC_{re.sub(r'[^A-Za-z0-9]+', '_', b.name).strip('_').upper()}"
                    tracks_batch.append({
                        "portfolio_id": pid,
                        "benchmark_id": bid,
                        **lineage,
                    })
        if tracks_batch:
            client.run_batch_write(MERGE_TRACKS, tracks_batch)
            stats.tracks_relationships = len(tracks_batch)
            logger.info(f"[DocIngest] Wrote {stats.tracks_relationships} TRACKS relationships")

    return stats
