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

# ISO 3166-1 alpha-2 mapping for iShares "Location" values
COUNTRY_MAP: dict[str, str] = {
    "netherlands": "NL", "germany": "DE", "france": "FR", "spain": "ES",
    "italy": "IT", "united kingdom": "GB", "switzerland": "CH", "sweden": "SE",
    "denmark": "DK", "finland": "FI", "belgium": "BE", "norway": "NO",
    "ireland": "IE", "austria": "AT", "portugal": "PT", "luxembourg": "LU",
    "united states": "US", "japan": "JP", "australia": "AU", "canada": "CA",
    "hong kong": "HK", "singapore": "SG", "south korea": "KR", "taiwan": "TW",
    "china": "CN", "india": "IN", "brazil": "BR", "mexico": "MX",
    "south africa": "ZA", "poland": "PL", "czech republic": "CZ",
    "hungary": "HU", "greece": "GR", "new zealand": "NZ", "israel": "IL",
}


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
        """Parse one ETF holdings CSV into domain models."""
        result = ETFTransformResult()
        etf_info = ISHARES_ETFS.get(ticker, {})

        if not etf_info:
            logger.error(f"Unknown ETF ticker: {ticker}")
            return result

        df = self._parse_ishares_csv(csv_path)
        if df is None or df.empty:
            logger.warning(f"No holdings data parsed from {csv_path}")
            return result

        as_of_date = self._extract_date(csv_path) or date.today()
        asset_class = AssetClass(etf_info["asset_class"])
        has_isin = "ISIN" in df.columns

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
            # Determine identifier: prefer ISIN, fall back to synthetic from ticker
            if has_isin:
                isin = self._clean_isin(row.get("ISIN", ""))
            else:
                isin = self._synthetic_isin(row.get("Ticker", ""))

            if not isin:
                continue

            name = str(row.get("Name", row.get("Issuer Name", "Unknown"))).strip()
            if not name or name in ("nan", "Unknown", "-", ""):
                continue

            weight = self._parse_float(row.get("Weight (%)", row.get("Weight", 0)))
            market_val = self._parse_float(
                row.get("Market Value", row.get("Notional Value", 0))
            )
            sector_name = str(row.get("Sector", "")).strip()
            if sector_name in ("nan", "", "-"):
                sector_name = ""

            # Map location to country code
            location = str(row.get("Location", row.get("Country", ""))).strip()
            country = self._map_country(location)

            asset_type_str = str(row.get("Asset Class", "Equity")).strip()
            asset_type = self._map_asset_type(asset_type_str)

            ticker_val = str(row.get("Ticker", "")).strip()
            if ticker_val in ("nan", ""):
                ticker_val = None

            currency = str(row.get("Market Currency", row.get("Currency", "EUR"))).strip()
            if currency in ("nan", ""):
                currency = "EUR"

            result.assets.append(
                Asset(
                    isin=isin,
                    name=name,
                    ticker=ticker_val,
                    asset_type=asset_type,
                    currency=currency[:3],
                    country=country,
                    sector=sector_name or None,
                )
            )

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
            text = csv_path.read_text(encoding="utf-8-sig", errors="replace")
            lines = text.strip().split("\n")

            # Find the header row
            header_idx = None
            for i, line in enumerate(lines):
                line_upper = line.upper()
                if "TICKER" in line_upper and "NAME" in line_upper:
                    header_idx = i
                    break
                if "ISIN" in line_upper and "WEIGHT" in line_upper:
                    header_idx = i
                    break

            if header_idx is None:
                logger.warning(f"Could not find header row in {csv_path}, trying auto-detect")
                return pd.read_csv(csv_path, encoding="utf-8-sig", on_bad_lines="skip")

            df = pd.read_csv(
                csv_path,
                skiprows=header_idx,
                encoding="utf-8-sig",
                on_bad_lines="skip",
                thousands=",",
            )

            # Clean column names
            df.columns = [c.strip() for c in df.columns]

            # Drop rows that are clearly not holdings (totals, disclaimers)
            if "Name" in df.columns:
                df = df.dropna(subset=["Name"])
                df = df[~df["Name"].astype(str).str.contains("Total|Disclaimer|Cash|^$", case=False, na=True)]

            # Drop rows where ISIN exists but is invalid
            if "ISIN" in df.columns:
                df = df.dropna(subset=["ISIN"])
                df = df[df["ISIN"].astype(str).str.len() == 12]

            return df

        except Exception as e:
            logger.error(f"Failed to parse {csv_path}: {e}")
            return None

    def _extract_date(self, csv_path: Path) -> date | None:
        """Try to extract the as-of date from the CSV header metadata."""
        try:
            with csv_path.open(encoding="utf-8-sig", errors="replace") as f:
                for line in f:
                    if "Fund Holdings as of" in line or "As Of Date" in line:
                        for part in line.split(","):
                            part = part.strip().strip('"').strip()
                            for fmt in ("%d/%b/%Y", "%b %d %Y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
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
    def _synthetic_isin(ticker_val: object) -> str | None:
        """Generate a synthetic ISIN-like identifier from a ticker when ISIN is unavailable."""
        t = str(ticker_val).strip().upper()
        if not t or t == "NAN" or len(t) < 1:
            return None
        # Remove spaces and special characters, keep only alphanumeric
        t = "".join(c for c in t if c.isalnum())
        if not t:
            return None
        # Pad to 10 chars with zeros, prefix with XX for synthetic
        padded = t[:10].ljust(10, "0")
        return f"XX{padded}"

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
    def _map_country(location: str) -> str | None:
        """Map iShares Location field to ISO 3166-1 alpha-2 code."""
        if not location or location in ("nan", "", "-"):
            return None
        loc_lower = location.lower()
        if loc_lower in COUNTRY_MAP:
            return COUNTRY_MAP[loc_lower]
        # Try partial match
        for key, code in COUNTRY_MAP.items():
            if key in loc_lower:
                return code
        # Return first 2 chars as fallback
        return location[:2].upper() if len(location) >= 2 else None

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
