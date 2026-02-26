"""Abstract base classes for pipeline components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel


class FetchResult(BaseModel):
    """Metadata about a completed fetch operation."""

    source: str
    file_path: str
    record_count: int
    from_cache: bool


class BaseFetcher(ABC):
    """Abstract base for all data fetchers.

    Each fetcher downloads data from one external source,
    stores it in data/raw/, and returns FetchResults.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    @abstractmethod
    def fetch(self) -> list[FetchResult]:
        """Download data from source. Returns list of FetchResults."""
        ...

    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name for logging."""
        ...
