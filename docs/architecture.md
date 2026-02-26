# Architecture

## System Overview

AMKG is a four-layer system:

1. **Data Pipeline** — Fetches real financial data, transforms, validates, and loads into Neo4j
2. **Graph Database** — Neo4j stores the knowledge graph with 10 node types and 12+ relationship types
3. **API Backend** — FastAPI serves REST endpoints and hosts the LLM chat agent
4. **Frontend** — React + Next.js delivers the interactive UI

## Data Flow

```
iShares CSVs ──→ ETFTransformer ──→ QualityValidator ──→ GraphLoader ──→ Neo4j
yfinance API ──→ AssetEnricher  ──↗
Kaggle ESG   ──→ ESGLoader     ──↗
```

## Graph Schema

Nodes:
- Portfolio, Benchmark, Asset, Sector, Holding
- ESGRating, Entity, FundManager, RatingProvider, PerformanceRecord

Relationships:
- (Portfolio)-[:TRACKS]->(Benchmark)
- (Portfolio)-[:HOLDS {weight_pct}]->(Asset)
- (Asset)-[:BELONGS_TO]->(Sector)
- (Asset)-[:HAS_ESG_SCORE]->(ESGRating)
- (Portfolio)-[:MANAGED_BY]->(FundManager)
- (Benchmark)-[:COMPOSED_OF {weight_pct}]->(Asset)
- (Portfolio)-[:PEER_OF]->(Portfolio)
- (Entity)-[:PARENT_OF]->(Entity)

## LLM Integration

Two-step pipeline:
1. User question → Claude generates Cypher query
2. Cypher executes against Neo4j → Claude formats results into natural language

Safety: All generated Cypher passes through a regex-based guardrail that blocks
CREATE, MERGE, SET, DELETE, REMOVE, DROP, CALL, LOAD CSV, FOREACH, and APOC procedures.

## Technology Choices

- **Neo4j** over PostgreSQL: Native graph traversal for relationship-heavy queries (peer overlap, shortest path, cross-entity concentration)
- **FastAPI** over Django/Flask: Async support, automatic OpenAPI docs, Pydantic integration
- **Claude** over GPT: Better at structured output (Cypher generation), native tool use support
- **Next.js** over Streamlit: Professional-grade UI, interactive graph visualization, better for portfolio showcase
- **react-force-graph-2d**: WebGL-accelerated force-directed graph rendering in the browser
