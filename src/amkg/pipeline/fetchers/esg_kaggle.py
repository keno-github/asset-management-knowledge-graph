"""Load ESG ratings from Kaggle public dataset.

The user downloads the Kaggle ESG CSV manually and places it in data/raw/esg/.
This fetcher validates the file exists and returns its path.

Expected CSV columns: company, ticker, esg_score, environment_score,
social_score, governance_score, controversy_level, etc.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from amkg.pipeline.base import BaseFetcher, FetchResult


class ESGKaggleLoader(BaseFetcher):
    """Load ESG data from a pre-downloaded Kaggle CSV."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir)
        self.esg_dir = data_dir / "raw" / "esg"
        self.esg_dir.mkdir(parents=True, exist_ok=True)

    def source_name(self) -> str:
        return "Kaggle ESG Dataset"

    def fetch(self) -> list[FetchResult]:
        """Check for ESG CSV files in data/raw/esg/ and return their paths."""
        results: list[FetchResult] = []
        csv_files = list(self.esg_dir.glob("*.csv"))

        if not csv_files:
            logger.warning(
                f"[ESG] No CSV files found in {self.esg_dir}. "
                "Download from Kaggle and place here."
            )
            return results

        for csv_path in csv_files:
            line_count = sum(1 for _ in csv_path.open()) - 1  # subtract header
            results.append(
                FetchResult(
                    source="Kaggle ESG",
                    file_path=str(csv_path),
                    record_count=line_count,
                    from_cache=True,
                )
            )
            logger.info(f"[ESG] Found {csv_path.name} with {line_count} records")

        return results
