"""Transform ESG data from Kaggle CSV and sector-based generation.

Two-source strategy:
1. Kaggle CSV — real ESG ratings matched by ticker to our assets
2. Sector-based fallback — generate realistic scores for uncovered assets
"""

from __future__ import annotations

import random
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from amkg.models.enums import ESGRiskLevel
from amkg.models.nodes import Asset, ESGRating

# Map Kaggle total_level (High ESG = Low risk) to our risk enum
_LEVEL_TO_RISK: dict[str, ESGRiskLevel] = {
    "High": ESGRiskLevel.LOW,
    "Medium": ESGRiskLevel.MEDIUM,
    "Low": ESGRiskLevel.HIGH,
}

# Map Kaggle total_grade to controversy score (higher = fewer controversies)
_GRADE_TO_CONTROVERSY: dict[str, int] = {
    "AAA": 5,
    "AA": 5,
    "A": 4,
    "BBB": 3,
    "BB": 2,
    "B": 1,
    "CCC": 0,
}

# Sector-based ESG profiles: (env, social, gov, risk_level)
# Scores on 0-10 scale, representing typical sector characteristics
SECTOR_ESG_PROFILES: dict[str, tuple[float, float, float, ESGRiskLevel]] = {
    "Technology": (6.5, 6.0, 7.0, ESGRiskLevel.LOW),
    "Financials": (5.0, 6.5, 7.5, ESGRiskLevel.LOW),
    "Health Care": (6.0, 7.0, 6.5, ESGRiskLevel.LOW),
    "Healthcare": (6.0, 7.0, 6.5, ESGRiskLevel.LOW),
    "Consumer Discretionary": (5.0, 5.5, 6.0, ESGRiskLevel.MEDIUM),
    "Consumer Staples": (5.5, 6.0, 6.5, ESGRiskLevel.LOW),
    "Industrials": (4.5, 5.5, 6.5, ESGRiskLevel.MEDIUM),
    "Communication Services": (5.5, 5.0, 6.0, ESGRiskLevel.MEDIUM),
    "Communication": (5.5, 5.0, 6.0, ESGRiskLevel.MEDIUM),
    "Communications": (5.5, 5.0, 6.0, ESGRiskLevel.MEDIUM),
    "Materials": (3.5, 5.0, 6.0, ESGRiskLevel.HIGH),
    "Energy": (3.0, 5.0, 6.0, ESGRiskLevel.HIGH),
    "Utilities": (4.0, 6.0, 6.5, ESGRiskLevel.MEDIUM),
    "Real Estate": (5.0, 5.5, 6.0, ESGRiskLevel.MEDIUM),
    "Basic Materials": (3.5, 5.0, 6.0, ESGRiskLevel.HIGH),
    "Consumer Cyclical": (5.0, 5.5, 6.0, ESGRiskLevel.MEDIUM),
    "Consumer Non-cyclical": (5.5, 6.0, 6.5, ESGRiskLevel.LOW),
}

# Default for unknown sectors
_DEFAULT_PROFILE = (5.0, 5.0, 5.5, ESGRiskLevel.MEDIUM)


class ESGTransformer:
    """Parse ESG data from Kaggle CSV and generate fallback scores."""

    def transform_kaggle(
        self,
        csv_path: Path,
        ticker_to_isin: dict[str, str],
    ) -> list[ESGRating]:
        """Parse Kaggle ESG CSV and match to our assets by ticker.

        Args:
            csv_path: Path to the Kaggle ESG CSV file
            ticker_to_isin: Mapping of uppercase ticker -> ISIN for our assets

        Returns:
            List of ESGRating objects for matched assets
        """
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig", on_bad_lines="skip")
        except Exception as e:
            logger.error(f"Failed to read ESG CSV {csv_path}: {e}")
            return []

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        if "ticker" not in df.columns or "total_score" not in df.columns:
            logger.error("ESG CSV missing required columns (ticker, total_score)")
            return []

        ratings: list[ESGRating] = []
        matched = 0

        for _, row in df.iterrows():
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker or ticker == "NAN":
                continue

            # Match to our assets
            isin = ticker_to_isin.get(ticker)
            if not isin:
                continue

            matched += 1

            # Normalize scores from ~0-700 range to 0-10
            env_raw = self._safe_float(row.get("environment_score", 0))
            soc_raw = self._safe_float(row.get("social_score", 0))
            gov_raw = self._safe_float(row.get("governance_score", 0))
            total_raw = self._safe_float(row.get("total_score", 0))

            env = min(env_raw / 70.0, 10.0)
            soc = min(soc_raw / 70.0, 10.0)
            gov = min(gov_raw / 70.0, 10.0)
            overall = min(total_raw / 210.0, 10.0)  # max ~2100/3 scores

            # Map risk level
            total_level = str(row.get("total_level", "Medium")).strip()
            risk = _LEVEL_TO_RISK.get(total_level, ESGRiskLevel.MEDIUM)

            # Map controversy score from grade
            grade = str(row.get("total_grade", "BB")).strip()
            controversy = _GRADE_TO_CONTROVERSY.get(grade, 2)

            # Taxonomy alignment from environment score (rough proxy)
            taxonomy_pct = min(env * 10.0, 100.0)  # 0-10 → 0-100%

            # Parse rating date
            rating_date = self._parse_date(row.get("last_processing_date"))

            ratings.append(
                ESGRating(
                    rating_id=f"ESG_{isin}",
                    entity_id=isin,
                    overall_score=round(overall, 2),
                    environmental_score=round(env, 2),
                    social_score=round(soc, 2),
                    governance_score=round(gov, 2),
                    risk_level=risk,
                    taxonomy_alignment_pct=round(taxonomy_pct, 1),
                    controversy_score=controversy,
                    rating_date=rating_date,
                    provider="Kaggle/Finnhub",
                )
            )

        logger.info(
            f"[ESG] Kaggle: {matched} assets matched out of {len(df)} rows"
        )
        return ratings

    def generate_sector_based(
        self,
        assets: list[Asset],
        covered_isins: set[str],
    ) -> list[ESGRating]:
        """Generate sector-based ESG scores for assets not covered by Kaggle.

        Uses realistic sector profiles with small random variation.
        """
        ratings: list[ESGRating] = []
        rng = random.Random(42)  # Fixed seed for reproducibility

        for asset in assets:
            if asset.isin in covered_isins:
                continue

            sector = asset.sector or ""
            profile = SECTOR_ESG_PROFILES.get(sector, _DEFAULT_PROFILE)
            env_base, soc_base, gov_base, risk = profile

            # Add small variation
            env = max(0, min(10, env_base + rng.uniform(-0.5, 0.5)))
            soc = max(0, min(10, soc_base + rng.uniform(-0.5, 0.5)))
            gov = max(0, min(10, gov_base + rng.uniform(-0.5, 0.5)))
            overall = (env + soc + gov) / 3.0

            # Controversy: based on risk level
            controversy_map = {
                ESGRiskLevel.NEGLIGIBLE: 5,
                ESGRiskLevel.LOW: 4,
                ESGRiskLevel.MEDIUM: 3,
                ESGRiskLevel.HIGH: 2,
                ESGRiskLevel.SEVERE: 1,
            }
            controversy = controversy_map.get(risk, 3)

            taxonomy_pct = min(env * 10.0, 100.0)

            ratings.append(
                ESGRating(
                    rating_id=f"ESG_{asset.isin}",
                    entity_id=asset.isin,
                    overall_score=round(overall, 2),
                    environmental_score=round(env, 2),
                    social_score=round(soc, 2),
                    governance_score=round(gov, 2),
                    risk_level=risk,
                    taxonomy_alignment_pct=round(taxonomy_pct, 1),
                    controversy_score=controversy,
                    rating_date=date(2022, 4, 1),
                    provider="Sector-based estimate",
                )
            )

        logger.info(
            f"[ESG] Sector-based: generated {len(ratings)} ratings for uncovered assets"
        )
        return ratings

    @staticmethod
    def _safe_float(val: object) -> float:
        if pd.isna(val):
            return 0.0
        try:
            return float(str(val).replace(",", "").strip())
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_date(val: object) -> date:
        if pd.isna(val):
            return date(2022, 4, 1)
        s = str(val).strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return date(2022, 4, 1)
