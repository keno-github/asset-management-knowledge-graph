"""Enrich assets with sector, industry, and market cap data from yfinance.

After iShares CSVs provide ticker/ISIN lists, this enricher calls
yfinance for each unique ticker to fill in sector classifications,
industry details, market cap, and country of listing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import yfinance as yf
from loguru import logger

from amkg.pipeline.cache import FileCache


class YFinanceEnricher:
    """Enrich asset tickers with fundamental data from Yahoo Finance."""

    def __init__(self, data_dir: Path, cache_ttl_hours: int = 168) -> None:
        """Initialize with a 7-day cache TTL (fundamentals don't change often)."""
        raw_dir = data_dir / "raw" / "yfinance"
        raw_dir.mkdir(parents=True, exist_ok=True)
        self.cache = FileCache(raw_dir, ttl_hours=cache_ttl_hours)
        self.rate_limit_delay = 0.5  # seconds between API calls

    def enrich_ticker(self, ticker: str) -> dict | None:
        """Fetch fundamental data for a single ticker.

        Returns dict with keys: sector, industry, country, exchange, market_cap, long_name
        or None if the ticker is not found.
        """
        cache_key = f"{ticker}.json"

        if self.cache.is_fresh(cache_key):
            cached_path = self.cache.get_path(cache_key)
            if cached_path.exists():
                return json.loads(cached_path.read_text())

        try:
            time.sleep(self.rate_limit_delay)
            info = yf.Ticker(ticker).info

            if not info or info.get("regularMarketPrice") is None:
                logger.warning(f"[yfinance] {ticker}: no data found")
                return None

            result = {
                "ticker": ticker,
                "long_name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country": info.get("country", ""),
                "exchange": info.get("exchange", ""),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", ""),
            }

            # Cache the result
            self.cache.get_path(cache_key).write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            self.cache.mark_fresh(cache_key, record_count=1)

            logger.debug(f"[yfinance] {ticker}: {result['sector']} / {result['industry']}")
            return result

        except Exception as e:
            logger.error(f"[yfinance] {ticker}: enrichment failed — {e}")
            return None

    def enrich_batch(self, tickers: list[str]) -> dict[str, dict]:
        """Enrich a list of tickers. Returns {ticker: enrichment_data}."""
        results: dict[str, dict] = {}
        total = len(tickers)

        for i, ticker in enumerate(tickers):
            if i % 20 == 0 and i > 0:
                logger.info(f"[yfinance] Progress: {i}/{total} tickers enriched")

            data = self.enrich_ticker(ticker)
            if data:
                results[ticker] = data

        logger.info(f"[yfinance] Enriched {len(results)}/{total} tickers")
        return results
