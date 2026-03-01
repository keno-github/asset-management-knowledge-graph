# AMKG — Asset Management Knowledge Graph

A full-stack knowledge graph for investment management. Models relationships between portfolios, benchmarks, asset classifications, ESG ratings, and performance metrics using real financial data from iShares ETFs, yfinance, and public ESG datasets.

Built on formal semantic web standards — OWL 2 ontology, SKOS controlled vocabularies, RDF export, SPARQL querying, and OWL-RL reasoning — with a Claude-powered natural language interface and unstructured document ingestion pipeline.

**Live:** [omoghakeno.dev](https://omoghakeno.dev)

**Author:** Keno Omogha

---

## Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │            React + Next.js Frontend            │
                    │  Dashboard · Portfolios · Graph Explorer       │
                    │  ESG Analysis · AI Chat · Doc Ingest           │
                    │  Ontology & Vocabularies                       │
                    └──────────────────┬────────────────────────────┘
                                       │ REST API
                    ┌──────────────────┴────────────────────────────┐
                    │            FastAPI Backend                      │
                    │  11 route modules · 30+ endpoints              │
                    │  ┌──────────────────────────────────────────┐  │
                    │  │  Claude LLM Agent (NL → Cypher)          │  │
                    │  │  Document Extractor (PDF → entities)     │  │
                    │  │  OWL-RL Reasoner (deductive inference)   │  │
                    │  │  RDF Exporter + SPARQL Engine            │  │
                    │  └──────────────────────────────────────────┘  │
                    └──────────────────┬────────────────────────────┘
                                       │ Bolt
                    ┌──────────────────┴────────────────────────────┐
                    │            Neo4j Knowledge Graph                │
                    │  5 node types · 7 relationship types           │
                    │  500+ real assets · 8 ETF portfolios           │
                    │  Provenance metadata on every entity           │
                    └──────────────────┬────────────────────────────┘
                                       ▲
                    ┌──────────────────┴────────────────────────────┐
                    │            Data Pipeline                        │
                    │  iShares ETFs → yfinance → ESG Kaggle          │
                    │  Fetch → Transform → Validate → Load           │
                    │  + Document ingestion (PDF/text → Claude → KG) │
                    └───────────────────────────────────────────────┘
```

---

## Features

### Data Pipeline
- Fetches real holdings from **8 iShares European ETFs** (MSCI Europe, EURO STOXX 50, MSCI World, ESG Enhanced, etc.)
- Enriches assets with sector, industry, and market cap via yfinance
- Integrates public ESG ratings from Kaggle datasets
- Data quality validation: ISIN format checks, weight sum validation, outlier detection
- File-based caching with TTL to avoid redundant downloads
- Every node and relationship carries provenance metadata (`_source`, `_ingested_at`, `_pipeline_run_id`)

### Document Ingestion
- Upload a PDF factsheet or paste raw text
- Claude extracts structured entities: portfolios, holdings, benchmarks, sectors
- Extracted data is written to Neo4j using the same MERGE queries as the main pipeline
- Full provenance tracking — documents are tagged with `_source: document_extraction`

### OWL 2 Ontology
- Formal ontology in Turtle format at `data/ontology/amkg.ttl`
- 5 classes: Portfolio, Asset, Benchmark, Sector, ESGRating
- 5 object properties: holds, tracks, belongsTo, composedOf, hasESGScore
- 21 datatype properties with XSD types
- Schema.org alignment (Portfolio → schema:InvestmentFund)
- Versioned with changelog

### SKOS Controlled Vocabularies
- **Sector vocabulary** — 11 GICS sectors with alternative labels for data harmonization (e.g., "Consumer Cyclical" maps to "Consumer Discretionary")
- **Asset class vocabulary** — 7 classes (Equity, Fixed Income, Multi-Asset, etc.)
- Downloadable as Turtle files

### RDF Export & SPARQL
- Export the full Neo4j graph as RDF triples in Turtle, JSON-LD, N-Triples, or RDF/XML
- In-memory SPARQL endpoint via rdflib — SELECT, ASK, CONSTRUCT queries
- Auto-injected PREFIX declarations so queries work out of the box
- No external triplestore required

### OWL-RL Reasoning
- Deductive closure over the ontology + live graph data
- Shows explicit vs. inferred triple counts
- Categorized inferences: type inheritance, domain/range inference, OWL axioms
- Example: Portfolio nodes inferred as schema:InvestmentFund via rdfs:subClassOf chains

### Graph Visualization
- Force-directed graph explorer with react-force-graph-2d
- Color-coded nodes by type, click to expand neighbors
- Node detail panel with properties
- Search and filter

### Natural Language Chat
- Ask questions in plain English: *"Which portfolios have the highest ESG risk?"*
- Claude generates Cypher → executes against Neo4j → formats the answer
- Read-only guardrails block any write operations
- Shows generated Cypher query and confidence score

### ESG Analytics
- Controversy exposure analysis
- Cross-portfolio ESG risk detection
- EU Taxonomy alignment scoring

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph Database | Neo4j 5.x |
| Backend | Python 3.10+, FastAPI, Pydantic v2 |
| LLM | Anthropic Claude (Sonnet 4) |
| Semantic Web | rdflib 7, owlrl 6, OWL 2 / SKOS / Turtle |
| Document Parsing | pdfplumber |
| Frontend | React 19, Next.js 16, TypeScript, Tailwind CSS |
| Graph Viz | react-force-graph-2d |
| Charts | Recharts |
| Testing | pytest (62 unit tests), ruff, mypy |
| Infrastructure | Docker Compose, Render, Vercel, Neo4j Aura |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for Neo4j)

### 1. Clone and install

```bash
git clone https://github.com/your-username/amkg.git
cd amkg

# Start Neo4j
docker compose up -d

# Install Python package
pip install -e ".[dev]"

# Install frontend
cd frontend && npm install && cd ..
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=knowledgegraph123
ANTHROPIC_API_KEY=sk-ant-...   # needed for chat + doc ingest
```

### 3. Run the pipeline

```bash
make ingest
```

This fetches iShares ETF data, enriches with yfinance, loads into Neo4j with full provenance metadata.

### 4. Start the app

```bash
# Terminal 1: Backend
make api
# → http://localhost:8000/docs

# Terminal 2: Frontend
make ui
# → http://localhost:3000
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check + Neo4j connectivity |
| `GET` | `/stats` | Node and relationship counts |
| `GET` | `/api/portfolios/` | List all portfolios |
| `GET` | `/api/portfolios/{id}` | Portfolio detail with benchmark and ESG |
| `GET` | `/api/portfolios/{id}/holdings` | Holdings with sector classifications |
| `GET` | `/api/portfolios/{id}/peer-overlap` | Peer overlap analysis |
| `GET` | `/api/benchmarks/{id}/sectors` | Benchmark sector breakdown |
| `GET` | `/api/benchmarks/overlap` | Constituent overlap between benchmarks |
| `GET` | `/api/esg/controversy` | ESG controversy exposure |
| `GET` | `/api/esg/cross-portfolio-risk` | Cross-portfolio ESG risk |
| `GET` | `/api/esg/taxonomy-alignment` | EU Taxonomy alignment |
| `GET` | `/api/discovery/graph-overview` | Node label distribution |
| `GET` | `/api/discovery/subgraph/{id}` | Neighborhood subgraph |
| `GET` | `/api/discovery/search-nodes` | Search nodes by name |
| `POST` | `/api/chat/` | Natural language → Cypher → answer |
| `POST` | `/api/ingest/extract` | Upload PDF or text → extract entities → write to graph |
| `GET` | `/ontology` | OWL ontology metadata |
| `GET` | `/ontology.ttl` | Download ontology (Turtle) |
| `GET` | `/ontology/versions` | Version history |
| `GET` | `/api/lineage/{label}/{id}` | Provenance metadata for any node |
| `GET` | `/api/vocabulary/sectors` | SKOS sector vocabulary |
| `GET` | `/api/vocabulary/asset-classes` | SKOS asset class vocabulary |
| `GET` | `/api/rdf/export` | Export graph as RDF (turtle, json-ld, n-triples, xml) |
| `GET` | `/api/rdf/sparql` | SPARQL query execution |
| `GET` | `/api/rdf/reasoning` | OWL-RL reasoning results |

---

## Graph Ontology

| Node | Description | Key Properties |
|------|-------------|----------------|
| `Portfolio` | Investment fund / ETF | name, ISIN, AUM, asset_class, morningstar_rating |
| `Asset` | Individual security | name, ISIN, country, sector, market_cap |
| `Benchmark` | Market index | name, provider, asset_class |
| `Sector` | GICS industry classification | name, level, skos_concept_uri |
| `ESGRating` | ESG risk assessment | overall_score, environmental, social, governance, risk_level |

**Relationships:** HOLDS, TRACKS, BELONGS_TO, COMPOSED_OF, HAS_ESG_SCORE

Every entity carries lineage metadata: `_source`, `_ingested_at`, `_pipeline_run_id`.

---

## Project Structure

```
amkg/
├── src/amkg/
│   ├── config.py                        # pydantic-settings
│   ├── models/                          # Pydantic v2 domain models
│   │   ├── nodes.py                     # Portfolio, Asset, Benchmark, etc.
│   │   ├── relationships.py             # HOLDS, TRACKS, etc.
│   │   └── enums.py                     # AssetClass, ESGRiskLevel
│   ├── pipeline/                        # ETL data pipeline
│   │   ├── orchestrator.py              # CLI: fetch → transform → validate → load
│   │   ├── fetchers/                    # iShares, yfinance, ESG data fetchers
│   │   ├── transformers/                # CSV → domain model transformers
│   │   ├── validators/                  # Data quality checks
│   │   ├── loader.py                    # Batch MERGE into Neo4j
│   │   ├── document_extractor.py        # PDF text extraction + Claude entity extraction
│   │   └── document_loader.py           # Write extracted entities to Neo4j
│   ├── graph/                           # Neo4j interaction
│   │   ├── client.py                    # Driver wrapper
│   │   ├── queries.py                   # Parameterized Cypher queries
│   │   └── schema.py                    # Index + constraint creation
│   ├── api/                             # FastAPI backend
│   │   ├── app.py                       # App factory with lifecycle
│   │   ├── deps.py                      # Dependency injection
│   │   ├── schemas.py                   # Request/response models
│   │   └── routes/                      # 11 route modules
│   ├── llm/                             # Claude integration
│   │   ├── cypher_agent.py              # NL → Cypher → execute → format
│   │   ├── prompts.py                   # Schema-aware system prompts
│   │   └── guardrails.py               # Read-only Cypher enforcement
│   └── rdf/                             # Semantic web layer
│       ├── exporter.py                  # Neo4j → RDF graph conversion
│       └── reasoner.py                  # OWL-RL deductive closure
├── frontend/
│   └── src/app/                         # 9 pages: dashboard, portfolios, graph,
│                                        #   ESG, chat, ingest, ontology, about
├── data/ontology/
│   ├── amkg.ttl                         # OWL 2 ontology (Turtle)
│   ├── sectors.ttl                      # SKOS sector vocabulary
│   └── asset-classes.ttl                # SKOS asset class vocabulary
├── tests/                               # 62 unit tests
│   └── unit/
│       ├── test_models.py               # Pydantic validation (38 tests)
│       ├── test_validators.py           # Data quality (9 tests)
│       └── test_guardrails.py           # Cypher safety (15 tests)
├── docker-compose.yml                   # Neo4j 5.x
├── pyproject.toml                       # PEP 621 metadata
├── Makefile                             # install, test, lint, api, ui, ingest
├── render.yaml                          # Render deployment blueprint
└── Procfile                             # Render start command
```

---

## Testing

```bash
# Unit tests
make test

# All tests including integration (requires running Neo4j)
make test-all

# Linting
make lint
```

---

## Example Chat Queries

```
"Which portfolios have the highest ESG risk?"
"What are the top 10 most held assets across all portfolios?"
"Show me the overlap between EURO STOXX 50 and MSCI Europe"
"Which sectors have the most cross-portfolio exposure?"
"What is the average ESG score across all portfolios?"
```

---

## Deployment

The app runs on three services:

| Component | Platform | URL |
|-----------|----------|-----|
| Frontend | Vercel | [omoghakeno.dev](https://omoghakeno.dev) |
| Backend | Render | API endpoint |
| Database | Neo4j Aura | Managed cloud instance |

See `.env.production.example` and `frontend/.env.production.example` for required environment variables.

---

## Data Sources

| Source | Data |
|--------|------|
| [iShares](https://www.ishares.com) | ETF holdings, portfolio compositions, weights |
| [yfinance](https://pypi.org/project/yfinance/) | Sector, industry, market cap, country |
| [Kaggle ESG](https://www.kaggle.com) | ESG scores and risk ratings |

---

## License

MIT
