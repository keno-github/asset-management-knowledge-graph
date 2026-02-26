"""Transform iShares ETF holdings CSVs into domain model instances.

iShares CSVs have a quirky format:
- First few lines contain fund metadata (name, date, etc.)
- Then a blank line separator
- Then the actual holdings table with headers
- Trailing lines with totals and disclaimers

This transformer handles that format and produces Portfolio, Benchmark,
Asset, Holding, and Sector domain objects from a single CSV file.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from amkg.models.enums import AssetClass, AssetType
from amkg.models.nodes import Asset, Benchmark, Holding, Portfolio
from amkg.pipeline.fetchers.ishares import ISHARES_ETFS


class ETFTransformResult:
    """Container for all domain objects extracted from one ETF CSV."""

    def __init__(self) -> None:
        self.portfolio: Portfolio | None = None
        self.benchmark: Benchmark | None = None
        self.assets: list[Asset] = []
        self.holdings: list[Holding] = []
        self.sectors: set[str] = set()


class ETFTransformer:
    """Parse iShares CSV files into graph-ready domain objects."""

    def transform(self, csv_path: Path, ticker: str) -> ETFTransformResult:
        """Parse one ETF holdings CSV into domain models.

        Args:
            csv_path: Path to the raw iShares CSV file.
            ticker: ETF ticker (e.g., "IMAE") used to look up metadata.

        Returns:
            ETFTransformResult with portfolio, benchmark, assets, and holdings.
        """
        result = ETFTransformResult()
        etf_info = ISHARES_ETFS.get(ticker, {})

        if not etf_info:
            logger.error(f"Unknown ETF ticker: {ticker}")
            return result

        # Parse the CSV — iShares format has metadata rows at the top
        df = self._parse_ishares_csv(csv_path)
        if df is None or df.empty:
            logger.warning(f"No holdings data parsed from {csv_path}")
            return result

        as_of_date = self._extract_date(csv_path) or date.today()
        asset_class = AssetClass(etf_info["asset_class"])

        # Create Portfolio node
        result.portfolio = Portfolio(
            portfolio_id=ticker,
            name=etf_info["name"],
            asset_class=asset_class,
            currency="EUR",
            inception_date=None,
            aum=None,
            is_active=True,
        )

        # Create Benchmark node
        result.benchmark = Benchmark(
            benchmark_id=f"BM_{ticker}",
            name=etf_info["benchmark"],
            ticker=None,
            provider=etf_info["benchmark_provider"],
            asset_class=asset_class,
            currency="EUR",
        )

        # Process each holding row
        for _, row in df.iterrows():
            isin = self._clean_isin(row.get("ISIN", ""))
            if not isin:
                continue

            name = str(row.get("Name", row.get("Issuer Name", "Unknown"))).strip()
            weight = self._parse_float(row.get("Weight (%)", row.get("Weight", 0)))
            market_val = self._parse_float(
                row.get("Market Value", row.get("Notional Value", 0))
            )
            sector_name = str(row.get("Sector", "")).strip()
            country = str(row.get("Location", row.get("Country", ""))).strip()
            asset_type_str = str(row.get("Asset Class", "Equity")).strip()

            # Determine asset type
            asset_type = self._map_asset_type(asset_type_str)

            # Create Asset
            ticker_val = str(row.get("Ticker", "")).strip() or None
            result.assets.append(
                Asset(
                    isin=isin,
                    name=name,
                    ticker=ticker_val,
                    asset_type=asset_type,
                    currency=str(row.get("Currency", "EUR")).strip()[:3] or "EUR",
                    country=country[:2] if len(country) >= 2 else None,
                    sector=sector_name or None,
                )
            )

            # Create Holding
            if weight > 0:
                result.holdings.append(
                    Holding(
                        portfolio_id=ticker,
                        isin=isin,
                        weight_pct=min(weight, 100.0),
                        market_value=market_val if market_val > 0 else None,
                        as_of_date=as_of_date,
                    )
                )

            # Track sectors
            if sector_name:
                result.sectors.add(sector_name)

        logger.info(
            f"[Transform] {ticker}: {len(result.assets)} assets, "
            f"{len(result.holdings)} holdings, {len(result.sectors)} sectors"
        )
        return result

    def _parse_ishares_csv(self, csv_path: Path) -> pd.DataFrame | None:
        """Parse iShares CSV, skipping metadata header rows."""
        try:
            text = csv_path.read_text(encoding="utf-8", errors="replace")
            lines = text.strip().split("\n")

            # Find the header row (first row with "Name" or "Ticker" in it)
            header_idx = None
            for i, line in enumerate(lines):
                if "Ticker" in line and ("Name" in line or "ISIN" in line):
                    header_idx = i
                    break
                if "ISIN" in line and "Weight" in line:
                    header_idx = i
                    break

            if header_idx is None:
                # Fallback: try reading with pandas auto-detection
                logger.warning(f"Could not find header row in {csv_path}, trying auto-detect")
                return pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")

            df = pd.read_csv(
                csv_path,
                skiprows=header_idx,
                encoding="utf-8",
                on_bad_lines="skip",
                thousands=",",
            )

            # Drop rows where ISIN is missing or clearly not a holding
            if "ISIN" in df.columns:
                df = df.dropna(subset=["ISIN"])
                df = df[df["ISIN"].str.len() == 12]

            return df

        except Exception as e:
            logger.error(f"Failed to parse {csv_path}: {e}")
            return None

    def _extract_date(self, csv_path: Path) -> date | None:
        """Try to extract the as-of date from the CSV header metadata."""
        try:
            with csv_path.open(encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "Fund Holdings as of" in line or "As Of Date" in line:
                        # Try to parse date from the line
                        for part in line.split(","):
                            part = part.strip().strip('"')
                            for fmt in ("%b %d %Y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
                                try:
                                    return datetime.strptime(part, fmt).date()
                                except ValueError:
                                    continue
        except Exception:
            pass
        return None

    @staticmethod
    def _clean_isin(raw: object) -> str | None:
        """Validate and clean an ISIN string."""
        s = str(raw).strip()
        if len(s) == 12 and s[:2].isalpha() and s[2:].isalnum():
            return s.upper()
        return None

    @staticmethod
    def _parse_float(val: object) -> float:
        """Safely parse a float from CSV values that may contain commas or blanks."""
        if pd.isna(val):
            return 0.0
        s = str(val).replace(",", "").replace("%", "").strip()
        try:
            return float(s)
        except ValueError:
            return 0.0

    @staticmethod
    def _map_asset_type(raw: str) -> AssetType:
        """Map iShares asset class strings to our AssetType enum."""
        raw_lower = raw.lower()
        if "equity" in raw_lower or "stock" in raw_lower:
            return AssetType.COMMON_STOCK
        if "bond" in raw_lower or "fixed" in raw_lower or "treasury" in raw_lower:
            return AssetType.GOVERNMENT_BOND
        if "corporate" in raw_lower:
            return AssetType.CORPORATE_BOND
        if "cash" in raw_lower or "money" in raw_lower:
            return AssetType.CASH
        if "reit" in raw_lower or "real estate" in raw_lower:
            return AssetType.REIT
        return AssetType.OTHER
