"""Application configuration using Pydantic Settings.

Loads from environment variables or a .env file in the project root.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "knowledgegraph123"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY: str = "dev-api-key-change-me"

    # LLM (Claude)
    ANTHROPIC_API_KEY: str = ""

    # Pipeline
    DATA_DIR: Path = Path("data")
    CACHE_TTL_HOURS: int = 24


settings = Settings()
