"""Pipeline orchestrator — runs fetch/transform/validate/load in sequence.

This is the main entry point for populating the knowledge graph with real data.

Usage:
    python -m amkg.pipeline.orchestrator --steps all
    python -m amkg.pipeline.orchestrator --steps fetch transform
    python -m amkg.pipeline.orchestrator --steps load
"""

from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from amkg.config import settings
from amkg.graph.client import Neo4jClient
from amkg.graph.schema import create_schema
from amkg.pipeline.fetchers.esg_kaggle import ESGKaggleLoader
from amkg.pipeline.fetchers.ishares import ISharesFetcher
from amkg.pipeline.fetchers.yfinance_enricher import YFinanceEnricher
from amkg.pipeline.loader import GraphLoader
from amkg.pipeline.transformers.esg_transformer import ESGTransformer
from amkg.pipeline.transformers.etf_transformer import ETFTransformer, ETFTransformResult
from amkg.pipeline.validators.quality import run_quality_checks


class PipelineOrchestrator:
    """Orchestrate the full data pipeline: fetch -> transform -> validate -> load."""

    def __init__(
        self,
        steps: list[str] | None = None,
        data_dir: Path | None = None,
        skip_yfinance: bool = False,
    ) -> None:
        self.steps = steps or ["all"]
        self.data_dir = data_dir or settings.DATA_DIR
        self.skip_yfinance = skip_yfinance
        self._transform_results: list[ETFTransformResult] = []
        self.run_id: str = str(uuid.uuid4())
        self.ingested_at: str = datetime.now(timezone.utc).isoformat()

    def run(self) -> dict:
        """Execute the pipeline and return a summary report."""
        report: dict = {}
        run_all = "all" in self.steps

        if "fetch" in self.steps or run_all:
            logger.info("=" * 60)
            logger.info("STEP 1/4: FETCHING RAW DATA")
            logger.info("=" * 60)
            report["fetch"] = self._fetch()

        if "transform" in self.steps or run_all:
            logger.info("=" * 60)
            logger.info("STEP 2/4: TRANSFORMING DATA")
            logger.info("=" * 60)
            report["transform"] = self._transform()

        if "validate" in self.steps or run_all:
            logger.info("=" * 60)
            logger.info("STEP 3/4: VALIDATING DATA QUALITY")
            logger.info("=" * 60)
            report["validate"] = self._validate()

        if "load" in self.steps or run_all:
            logger.info("=" * 60)
            logger.info("STEP 4/4: LOADING INTO NEO4J")
            logger.info("=" * 60)
            report["load"] = self._load()

        report["lineage"] = {
            "run_id": self.run_id,
            "ingested_at": self.ingested_at,
        }
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"Run ID: {self.run_id}")
        logger.info(f"Summary: {report}")
        logger.info("=" * 60)
        return report

    def _fetch(self) -> dict:
        """Step 1: Download raw data from all sources."""
        ishares = ISharesFetcher(
            self.data_dir, cache_ttl_hours=settings.CACHE_TTL_HOURS
        )
        results = ishares.fetch()
        return {
            "ishares_files": len(results),
            "total_records": sum(r.record_count for r in results),
            "from_cache": sum(1 for r in results if r.from_cache),
        }

    def _transform(self) -> dict:
        """Step 2: Transform raw CSVs into domain models."""
        transformer = ETFTransformer()
        ishares_dir = self.data_dir / "raw" / "ishares"

        self._transform_results = []
        total_assets = 0
        total_holdings = 0

        for csv_file in sorted(ishares_dir.glob("*_holdings.csv")):
            ticker = csv_file.stem.replace("_holdings", "")
            result = transformer.transform(csv_file, ticker)
            if result.portfolio:
                self._transform_results.append(result)
                total_assets += len(result.assets)
                total_holdings += len(result.holdings)

        return {
            "etfs_processed": len(self._transform_results),
            "total_assets": total_assets,
            "total_holdings": total_holdings,
        }

    def _validate(self) -> dict:
        """Step 3: Run data quality checks."""
        all_holdings = []
        all_isins = []

        for result in self._transform_results:
            all_holdings.extend(result.holdings)
            all_isins.extend(a.isin for a in result.assets)

        report = run_quality_checks(all_holdings, all_isins)

        if not report.is_acceptable:
            logger.error(f"Quality check FAILED: {report.errors}")

        return {
            "total_checks": report.total_checks,
            "passed": report.passed,
            "pass_rate": f"{report.pass_rate:.1%}",
            "warnings": len(report.warnings),
            "errors": len(report.errors),
            "acceptable": report.is_acceptable,
        }

    def _load(self) -> dict:
        """Step 4: Load validated data into Neo4j."""
        client = Neo4jClient()

        if not client.verify_connectivity():
            logger.error("Cannot connect to Neo4j. Is it running? (docker-compose up -d)")
            return {"error": "Neo4j not reachable"}

        try:
            # Create schema (indexes + constraints)
            create_schema(client)

            loader = GraphLoader(
                client, run_id=self.run_id, ingested_at=self.ingested_at
            )
            counts: dict[str, int] = {}

            # Collect all objects across ETFs
            all_portfolios = []
            all_benchmarks = []
            all_assets = []
            all_holdings = []
            all_sectors: set[str] = set()
            track_pairs: list[tuple[str, str]] = []
            asset_sector_pairs: list[tuple[str, str]] = []

            for result in self._transform_results:
                if result.portfolio:
                    all_portfolios.append(result.portfolio)
                if result.benchmark:
                    all_benchmarks.append(result.benchmark)
                all_assets.extend(result.assets)
                all_holdings.extend(result.holdings)
                all_sectors.update(result.sectors)

                if result.portfolio and result.benchmark:
                    track_pairs.append(
                        (result.portfolio.portfolio_id, result.benchmark.benchmark_id)
                    )

                for asset in result.assets:
                    if asset.sector:
                        asset_sector_pairs.append((asset.isin, asset.sector))

            # Load nodes
            counts["portfolios"] = loader.load_portfolios(all_portfolios)
            counts["benchmarks"] = loader.load_benchmarks(all_benchmarks)
            counts["assets"] = loader.load_assets(all_assets)
            counts["sectors"] = loader.load_sectors(all_sectors)

            # Load relationships
            counts["holds"] = loader.load_holdings(all_holdings)
            counts["tracks"] = loader.load_tracks(track_pairs)
            counts["belongs_to"] = loader.load_belongs_to(asset_sector_pairs)

            # Load benchmark compositions (ETF holdings = benchmark constituents)
            for result in self._transform_results:
                if result.benchmark and result.holdings:
                    loader.load_composed_of(result.benchmark.benchmark_id, result.holdings)

            # Enrich with yfinance (optional, slow)
            if not self.skip_yfinance:
                tickers = [
                    a.ticker for a in all_assets if a.ticker and len(a.ticker) <= 10
                ]
                unique_tickers = list(set(tickers))[:100]  # cap at 100 for speed

                if unique_tickers:
                    logger.info(f"Enriching {len(unique_tickers)} tickers via yfinance...")
                    enricher = YFinanceEnricher(self.data_dir)
                    enrichments = enricher.enrich_batch(unique_tickers)
                    if enrichments:
                        counts["yfinance_enriched"] = loader.enrich_assets_from_yfinance(
                            enrichments
                        )

            # Load ESG ratings (Kaggle CSV + sector-based fallback)
            logger.info("Loading ESG ratings...")
            esg_transformer = ESGTransformer()

            # Build ticker -> ISIN mapping from our assets
            ticker_to_isin: dict[str, str] = {}
            for a in all_assets:
                if a.ticker:
                    ticker_to_isin[a.ticker.upper()] = a.isin

            all_esg_ratings = []

            # Try Kaggle CSV first
            esg_fetcher = ESGKaggleLoader(self.data_dir)
            esg_files = esg_fetcher.fetch()
            for esg_result in esg_files:
                kaggle_ratings = esg_transformer.transform_kaggle(
                    Path(esg_result.file_path), ticker_to_isin
                )
                all_esg_ratings.extend(kaggle_ratings)

            # Generate sector-based ESG for uncovered assets
            covered_isins = {r.entity_id for r in all_esg_ratings}
            # Deduplicate assets by ISIN
            unique_assets = list({a.isin: a for a in all_assets}.values())
            sector_ratings = esg_transformer.generate_sector_based(
                unique_assets, covered_isins
            )
            all_esg_ratings.extend(sector_ratings)

            if all_esg_ratings:
                counts["esg_ratings"] = loader.load_esg_ratings(all_esg_ratings)
                counts["esg_relationships"] = loader.load_has_esg_score(all_esg_ratings)

            # Final stats
            stats = client.get_stats()
            counts["graph_stats"] = stats

            return counts

        finally:
            client.close()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AMKG Data Pipeline")
    parser.add_argument(
        "--steps",
        nargs="+",
        default=["all"],
        choices=["fetch", "transform", "validate", "load", "all"],
        help="Pipeline steps to run",
    )
    parser.add_argument(
        "--skip-yfinance",
        action="store_true",
        help="Skip yfinance enrichment (faster but less data)",
    )
    args = parser.parse_args()

    orchestrator = PipelineOrchestrator(
        steps=args.steps, skip_yfinance=args.skip_yfinance
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
