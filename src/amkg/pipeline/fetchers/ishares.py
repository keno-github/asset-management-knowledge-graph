"""Fetch iShares ETF holdings CSVs from the iShares website.

iShares publishes daily holdings for all their ETFs as downloadable CSVs.
Each CSV gives us Portfolio, Benchmark, Asset, and Holding data in one file.

Target ETFs are European-focused to match the asset management domain:
- Core MSCI Europe, EURO STOXX 50, Core MSCI World, ESG Enhanced, etc.
"""

from __future__ import annotations

from pathlib import Path

import requests
from loguru import logger

from amkg.pipeline.base import BaseFetcher, FetchResult
from amkg.pipeline.cache import FileCache

# iShares UK ETF product pages with CSV download endpoints.
# Format: ticker -> (product_page_id, fund_slug, description, benchmark_name)
ISHARES_ETFS: dict[str, dict[str, str]] = {
    "IMAE": {
        "url": "https://www.ishares.com/uk/individual/en/products/251882/ishares-msci-europe-ucits-etf-acc-fund/1478358488498.ajax?fileType=csv&fileName=IMAE_holdings&dataType=fund",
        "name": "iShares Core MSCI Europe UCITS ETF",
        "benchmark": "MSCI Europe",
        "benchmark_provider": "MSCI",
        "asset_class": "Equity",
    },
    "EUE": {
        "url": "https://www.ishares.com/uk/individual/en/products/251900/ishares-euro-stoxx-50-ucits-etf-dist-fund/1478358488498.ajax?fileType=csv&fileName=EUE_holdings&dataType=fund",
        "name": "iShares EURO STOXX 50 UCITS ETF (DE)",
        "benchmark": "EURO STOXX 50",
        "benchmark_provider": "STOXX",
        "asset_class": "Equity",
    },
    "SWDA": {
        "url": "https://www.ishares.com/uk/individual/en/products/251882/ishares-msci-world-ucits-etf-acc-fund/1478358488498.ajax?fileType=csv&fileName=SWDA_holdings&dataType=fund",
        "name": "iShares Core MSCI World UCITS ETF",
        "benchmark": "MSCI World",
        "benchmark_provider": "MSCI",
        "asset_class": "Equity",
    },
    "EDMW": {
        "url": "https://www.ishares.com/uk/individual/en/products/288180/ishares-msci-europe-esg-enhanced-ucits-etf-eur-acc-fund/1478358488498.ajax?fileType=csv&fileName=EDMW_holdings&dataType=fund",
        "name": "iShares MSCI Europe ESG Enhanced UCITS ETF",
        "benchmark": "MSCI Europe ESG Enhanced Focus",
        "benchmark_provider": "MSCI",
        "asset_class": "Equity",
    },
    "IEAG": {
        "url": "https://www.ishares.com/uk/individual/en/products/251740/ishares-euro-aggregate-bond-ucits-etf/1478358488498.ajax?fileType=csv&fileName=IEAG_holdings&dataType=fund",
        "name": "iShares Core Euro Aggregate Bond UCITS ETF",
        "benchmark": "Bloomberg Euro Aggregate",
        "benchmark_provider": "Bloomberg",
        "asset_class": "Fixed Income",
    },
    "EXS1": {
        "url": "https://www.ishares.com/uk/individual/en/products/251464/ishares-core-dax-ucits-etf-de-fund/1478358488498.ajax?fileType=csv&fileName=EXS1_holdings&dataType=fund",
        "name": "iShares Core DAX UCITS ETF (DE)",
        "benchmark": "DAX",
        "benchmark_provider": "Deutsche Boerse",
        "asset_class": "Equity",
    },
    "IESE": {
        "url": "https://www.ishares.com/uk/individual/en/products/280510/ishares-msci-europe-sri-ucits-etf-fund/1478358488498.ajax?fileType=csv&fileName=IESE_holdings&dataType=fund",
        "name": "iShares MSCI Europe SRI UCITS ETF",
        "benchmark": "MSCI Europe SRI Select Reduced Fossil Fuel",
        "benchmark_provider": "MSCI",
        "asset_class": "Equity",
    },
    "CSEMU": {
        "url": "https://www.ishares.com/uk/individual/en/products/290846/ishares-core-msci-emu-ucits-etf-eur-acc-fund/1478358488498.ajax?fileType=csv&fileName=CSEMU_holdings&dataType=fund",
        "name": "iShares Core MSCI EMU UCITS ETF",
        "benchmark": "MSCI EMU",
        "benchmark_provider": "MSCI",
        "asset_class": "Equity",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/csv,text/plain,*/*",
}


class ISharesFetcher(BaseFetcher):
    """Download iShares ETF holdings CSVs for European ETFs."""

    def __init__(self, data_dir: Path, cache_ttl_hours: int = 24) -> None:
        super().__init__(data_dir)
        raw_dir = data_dir / "raw" / "ishares"
        raw_dir.mkdir(parents=True, exist_ok=True)
        self.cache = FileCache(raw_dir, ttl_hours=cache_ttl_hours)

    def source_name(self) -> str:
        return "iShares ETF Holdings"

    def fetch(self) -> list[FetchResult]:
        """Download holdings CSVs for all target ETFs."""
        results: list[FetchResult] = []

        for ticker, info in ISHARES_ETFS.items():
            cache_key = f"{ticker}_holdings.csv"

            if self.cache.is_fresh(cache_key):
                logger.info(f"[iShares] {ticker}: using cached data")
                path = self.cache.get_path(cache_key)
                line_count = sum(1 for _ in path.open()) if path.exists() else 0
                results.append(
                    FetchResult(
                        source=f"iShares:{ticker}",
                        file_path=str(path),
                        record_count=line_count,
                        from_cache=True,
                    )
                )
                continue

            logger.info(f"[iShares] {ticker}: downloading holdings...")
            try:
                resp = requests.get(info["url"], headers=HEADERS, timeout=30)
                resp.raise_for_status()

                file_path = self.cache.get_path(cache_key)
                file_path.write_text(resp.text, encoding="utf-8")

                line_count = resp.text.count("\n")
                self.cache.mark_fresh(cache_key, record_count=line_count)

                results.append(
                    FetchResult(
                        source=f"iShares:{ticker}",
                        file_path=str(file_path),
                        record_count=line_count,
                        from_cache=False,
                    )
                )
                logger.info(f"[iShares] {ticker}: saved {line_count} lines")

            except requests.RequestException as e:
                logger.error(f"[iShares] {ticker}: download failed — {e}")

        return results
