"""Neo4j driver wrapper with session management and batch operations.

Provides a clean interface for the rest of the application to interact
with Neo4j without dealing with driver/session lifecycle directly.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from loguru import logger
from neo4j import Driver, GraphDatabase, Session

from amkg.config import settings


class Neo4jClient:
    """Manages Neo4j connection lifecycle and provides query helpers.

    Usage:
        client = Neo4jClient()
        results = client.run_query("MATCH (n:Portfolio) RETURN n LIMIT 10")
        client.close()
    """

    def __init__(
        self,
        uri: str = settings.NEO4J_URI,
        user: str = settings.NEO4J_USER,
        password: str = settings.NEO4J_PASSWORD,
    ) -> None:
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Neo4j client initialized for {uri}")

    def close(self) -> None:
        """Close the underlying driver connection."""
        self._driver.close()
        logger.info("Neo4j connection closed")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Yield a Neo4j session with automatic cleanup."""
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def verify_connectivity(self) -> bool:
        """Test that the Neo4j instance is reachable."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def run_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a read-only Cypher query and return results as dicts."""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def run_write(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Execute a write transaction."""
        with self.session() as session:
            session.execute_write(lambda tx: tx.run(query, parameters or {}))

    def run_batch_write(
        self, query: str, batch: list[dict[str, Any]]
    ) -> None:
        """Execute a batch write using UNWIND for performance.

        The query should reference $batch and use UNWIND:
            UNWIND $batch AS row
            MERGE (n:Label {id: row.id})
            SET n.name = row.name
        """
        if not batch:
            return
        with self.session() as session:
            session.execute_write(lambda tx: tx.run(query, {"batch": batch}))
        logger.debug(f"Batch write: {len(batch)} records")

    def clear_database(self) -> None:
        """Delete all nodes and relationships. Use with caution."""
        self.run_write("MATCH (n) DETACH DELETE n")
        logger.warning("Database cleared — all nodes and relationships deleted")

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Return node and relationship counts by label/type."""
        nodes = self.run_query(
            "MATCH (n) RETURN labels(n)[0] AS label, COUNT(*) AS count"
        )
        rels = self.run_query(
            "MATCH ()-[r]->() RETURN type(r) AS type, COUNT(*) AS count"
        )
        return {
            "nodes": {r["label"]: r["count"] for r in nodes},
            "relationships": {r["type"]: r["count"] for r in rels},
        }
