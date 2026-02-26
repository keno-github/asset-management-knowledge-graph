# AMKG — Asset Management Knowledge Graph

A full-stack knowledge graph system that models relationships between **investment portfolios, benchmarks, asset classifications, ESG ratings, and performance metrics** using real financial data from iShares ETFs, yfinance, and public ESG datasets.

**Author:** Keno Omogha — Lead Analytics Engineer, Asset Management

---

## Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │              React + Next.js Frontend        │
                    │  Dashboard │ Portfolios │ Graph │ ESG │ Chat │
                    └──────────────────┬───────────────────────────┘
                                       │ REST API
                    ┌──────────────────┴───────────────────────────┐
                    │              FastAPI Backend                  │
                    │  Portfolios │ Benchmarks │ ESG │ Discovery   │
                    │  ┌─────────────────────────────────────┐     │
                    │  │  Claude LLM Agent (NL → Cypher)     │     │
                    │  │  Guardrails (read-only enforcement) │     │
                    │  └─────────────────────────────────────┘     │
                    └──────────────────┬───────────────────────────┘
                                       │ Bolt Protocol
                    ┌──────────────────┴───────────────────────────┐
                    │              Neo4j Knowledge Graph            │
                    │  10 node types · 12+ relationship types      │
                    │  500+ real assets · 8 ETF portfolios         │
                    └──────────────────────────────────────────────┘
                                       ▲
                    ┌──────────────────┴───────────────────────────┐
                    │              Data Pipeline                    │
                    │  iShares ETFs → yfinance → ESG Kaggle        │
                    │  Fetch → Transform → Validate → Load         │
                    └──────────────────────────────────────────────┘
```

## Key Features

### 1. Real Data Pipeline
- Fetches holdings from **8 iShares European ETFs** (MSCI Europe, EURO STOXX 50, MSCI World, ESG Enhanced, etc.)
- Enriches assets with **sector, industry, and market cap** via yfinance
- Integrates **public ESG ratings** from Kaggle datasets
- **Data quality validation**: ISIN format checks, weight sum validation, outlier detection
- File-based caching with TTL to avoid redundant downloads

### 2. Interactive Graph Visualization
- Force-directed graph explorer with **react-force-graph-2d**
- Color-coded nodes by type (Portfolio, Asset, Benchmark, ESG, etc.)
- Click-to-expand neighbors, zoom/pan, filter by node type
- Node detail panel with properties on click

### 3. LLM-Powered Natural Language Chat
- Ask questions in plain English: *"Which portfolios have the highest ESG risk?"*
- Two-step pipeline: Claude generates Cypher → executes against Neo4j → formats answer
- **Read-only guardrails** block any write operations in generated Cypher
- Transparent: shows generated Cypher query with confidence score

## Graph Ontology

| Node | Description | Key Properties |
|------|-------------|----------------|
| `Portfolio` | Investment fund/ETF | name, ISIN, AUM, asset_class, morningstar_rating |
| `Benchmark` | Market index | name, provider, asset_class |
| `Asset` | Individual security | name, ISIN, country, asset_type |
| `Sector` | Industry classification | name, level (1-4 GICS hierarchy) |
| `ESGRating` | ESG risk assessment | environment_score, social_score, governance_score, risk_level |
| `Entity` | Corporate entity (LEI) | name, lei, jurisdiction |
| `FundManager` | Portfolio manager | name, firm |
| `Holding` | Portfolio-asset edge data | weight_pct, as_of_date |
| `PerformanceRecord` | Return data | period, return_pct, benchmark_return |
| `RatingProvider` | ESG/ratings agency | name, methodology |

**Relationships:** TRACKS, HOLDS, BELONGS_TO, HAS_PERFORMANCE, MEASURED_AGAINST, HAS_ESG_SCORE, RATED_BY, MANAGED_BY, WORKS_FOR, COMPOSED_OF, PEER_OF, PARENT_OF

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph Database | Neo4j 5.x Community Edition |
| Backend | Python 3.11+, FastAPI, Pydantic v2, pydantic-settings |
| LLM | Anthropic Claude (Sonnet) via `anthropic` SDK |
| Data Pipeline | iShares CSV fetcher, yfinance, pandas |
| Frontend | React 19, Next.js 16, TypeScript, Tailwind CSS |
| Graph Viz | react-force-graph-2d |
| Charts | Recharts |
| Testing | pytest (62 unit tests), ruff linting |
| Infrastructure | Docker Compose (Neo4j) |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for Neo4j)

### 1. Clone and Install

```bash
git clone <repo-url>
cd amkg

# Start Neo4j
docker compose up -d

# Install Python package
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings:
#   NEO4J_PASSWORD=your-password
#   ANTHROPIC_API_KEY=sk-ant-...  (for chat feature)
```

### 3. Run the Pipeline

```bash
make ingest
# Fetches iShares ETF data, enriches with yfinance, loads into Neo4j
```

### 4. Start the Application

```bash
# Terminal 1: API server
make api
# → http://localhost:8000/docs (OpenAPI interactive docs)

# Terminal 2: Frontend
make ui
# → http://localhost:3000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + Neo4j connectivity |
| GET | `/stats` | Graph node/relationship counts |
| GET | `/api/portfolios/` | List all portfolios |
| GET | `/api/portfolios/{id}` | Portfolio detail |
| GET | `/api/portfolios/{id}/holdings` | Portfolio holdings with sectors |
| GET | `/api/portfolios/{id}/peer-overlap` | Peer overlap analysis |
| GET | `/api/esg/controversy` | ESG controversy exposure |
| GET | `/api/esg/cross-portfolio-risk` | Cross-portfolio ESG risk |
| GET | `/api/esg/taxonomy-alignment` | EU Taxonomy alignment |
| GET | `/api/discovery/graph-overview` | Node label distribution |
| GET | `/api/discovery/subgraph/{id}` | Subgraph around a node |
| POST | `/api/chat/` | Natural language question → answer |

## Project Structure

```
amkg/
├── src/amkg/
│   ├── config.py                     # pydantic-settings config
│   ├── models/                       # Pydantic v2 domain models
│   │   ├── nodes.py                  # 10 node types with validation
│   │   ├── relationships.py          # 12 relationship types
│   │   └── enums.py                  # AssetClass, ESGRiskLevel, etc.
│   ├── pipeline/                     # ETL data pipeline
│   │   ├── orchestrator.py           # CLI: fetch → transform → validate → load
│   │   ├── fetchers/                 # iShares, yfinance, ESG data fetchers
│   │   ├── transformers/             # CSV → domain model transformers
│   │   ├── validators/               # Data quality checks
│   │   └── loader.py                 # Batch MERGE into Neo4j
│   ├── graph/                        # Neo4j interaction
│   │   ├── client.py                 # Driver wrapper with batch ops
│   │   ├── queries.py                # 16+ parameterized Cypher queries
│   │   └── schema.py                 # Index + constraint creation
│   ├── api/                          # FastAPI backend
│   │   ├── app.py                    # App factory with lifespan
│   │   └── routes/                   # portfolios, benchmarks, esg, discovery, chat
│   └── llm/                          # LLM integration
│       ├── cypher_agent.py           # NL → Cypher → execute → format
│       ├── prompts.py                # Schema-aware system prompts
│       └── guardrails.py             # Read-only Cypher enforcement
├── frontend/                         # React + Next.js
│   └── src/app/                      # Dashboard, Portfolios, Graph, ESG, Chat
├── tests/                            # 62 unit tests
│   ├── unit/
│   │   ├── test_models.py            # Pydantic validation (38 tests)
│   │   ├── test_validators.py        # Data quality (9 tests)
│   │   └── test_guardrails.py        # Cypher safety (15 tests)
│   └── conftest.py                   # Test fixtures
├── docker-compose.yml                # Neo4j 5.x
├── pyproject.toml                    # PEP 621 metadata
└── Makefile                          # install, test, lint, api, ui, ingest
```

## Testing

```bash
# Unit tests only
make test

# All tests (including integration — requires running Neo4j)
make test-all

# Linting
make lint
```

## Example Chat Queries

```
"Which portfolios have the highest ESG risk?"
"What are the top 10 most held assets across all portfolios?"
"Show me the overlap between EURO STOXX 50 and MSCI Europe portfolios"
"Which sectors have the most cross-portfolio exposure?"
"What is the average ESG score across all portfolios?"
```

## Data Sources

| Source | Type | Data Provided |
|--------|------|---------------|
| [iShares](https://www.ishares.com) | ETF Holdings CSVs | Portfolio compositions, weights, ISINs |
| [yfinance](https://pypi.org/project/yfinance/) | Python API | Sector, industry, market cap, country |
| [Kaggle ESG](https://www.kaggle.com) | Public CSV | ESG scores and risk ratings |

## License

MIT
