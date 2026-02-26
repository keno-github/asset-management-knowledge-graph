"""File-based cache with TTL to prevent redundant data downloads.

Each cached item consists of a data file and a .meta.json sidecar
that records when the file was fetched and how many records it contains.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger


class FileCache:
    """Prevents redundant downloads by checking file age against TTL."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24) -> None:
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.meta.json"

    def is_fresh(self, key: str) -> bool:
        """Check if cached data exists and is within TTL."""
        meta_path = self._meta_path(key)
        if not meta_path.exists():
            return False
        try:
            meta = json.loads(meta_path.read_text())
            fetched_at = datetime.fromisoformat(meta["fetched_at"])
            return datetime.now() - fetched_at < timedelta(hours=self.ttl_hours)
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def get_path(self, key: str) -> Path:
        """Return the data file path for a cache key."""
        return self.cache_dir / key

    def mark_fresh(self, key: str, record_count: int = 0) -> None:
        """Write cache metadata after a successful fetch."""
        meta = {
            "fetched_at": datetime.now().isoformat(),
            "record_count": record_count,
        }
        self._meta_path(key).write_text(json.dumps(meta, indent=2))
        logger.debug(f"Cache marked fresh: {key} ({record_count} records)")
