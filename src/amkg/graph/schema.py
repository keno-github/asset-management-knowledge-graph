"""Neo4j schema management: indexes and constraints.

Run once during initial setup or after a database reset to ensure
query performance on key lookup fields.
"""

from loguru import logger

from amkg.graph.client import Neo4jClient

INDEXES = [
    "CREATE INDEX IF NOT EXISTS FOR (p:Portfolio) ON (p.portfolio_id)",
    "CREATE INDEX IF NOT EXISTS FOR (p:Portfolio) ON (p.isin)",
    "CREATE INDEX IF NOT EXISTS FOR (b:Benchmark) ON (b.benchmark_id)",
    "CREATE INDEX IF NOT EXISTS FOR (a:Asset) ON (a.isin)",
    "CREATE INDEX IF NOT EXISTS FOR (a:Asset) ON (a.ticker)",
    "CREATE INDEX IF NOT EXISTS FOR (s:Sector) ON (s.sector_id)",
    "CREATE INDEX IF NOT EXISTS FOR (s:Sector) ON (s.name)",
    "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.entity_id)",
    "CREATE INDEX IF NOT EXISTS FOR (f:FundManager) ON (f.manager_id)",
    "CREATE INDEX IF NOT EXISTS FOR (r:RatingProvider) ON (r.provider_id)",
    "CREATE INDEX IF NOT EXISTS FOR (esg:ESGRating) ON (esg.rating_id)",
    "CREATE INDEX IF NOT EXISTS FOR (pr:PerformanceRecord) ON (pr.record_id)",
]

CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Asset) REQUIRE a.isin IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Portfolio) REQUIRE p.portfolio_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Benchmark) REQUIRE b.benchmark_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.sector_id IS UNIQUE",
]


def create_schema(client: Neo4jClient) -> None:
    """Create all indexes and constraints."""
    for stmt in CONSTRAINTS:
        client.run_write(stmt)
    logger.info(f"Created {len(CONSTRAINTS)} constraints")

    for stmt in INDEXES:
        client.run_write(stmt)
    logger.info(f"Created {len(INDEXES)} indexes")
