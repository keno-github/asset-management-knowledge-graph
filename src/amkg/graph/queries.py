"""Parameterized Cypher query library for asset management analytics.

These queries demonstrate the power of graph-based analytics for investment
management — answering relationship questions that would require complex
multi-table joins or be impossible in traditional relational SQL.

All queries use parameters ($variable) to prevent injection and enable caching.
"""

# ============================================================
# PORTFOLIO EXPLORATION
# ============================================================

LIST_PORTFOLIOS = """
MATCH (p:Portfolio)
OPTIONAL MATCH (p)-[:TRACKS]->(b:Benchmark)
RETURN p.portfolio_id AS portfolio_id, p.name AS name,
       p.asset_class AS asset_class, p.aum AS aum,
       p.morningstar_rating AS morningstar_rating,
       p.as_of_date AS as_of_date,
       b.name AS benchmark
ORDER BY p.name
"""

PORTFOLIO_FULL_PROFILE = """
MATCH (p:Portfolio {portfolio_id: $portfolio_id})
OPTIONAL MATCH (p)-[:TRACKS]->(b:Benchmark)
OPTIONAL MATCH (p)-[:MANAGED_BY]->(fm:FundManager)-[:WORKS_FOR]->(e:Entity)
OPTIONAL MATCH (p)-[:HAS_ESG_SCORE]->(esg:ESGRating)
RETURN p.portfolio_id AS portfolio_id, p.name AS name,
       p.asset_class AS asset_class, p.aum AS aum,
       p.morningstar_rating AS morningstar_rating,
       p.as_of_date AS as_of_date,
       b.name AS benchmark, b.benchmark_id AS benchmark_id,
       fm.name AS manager, e.name AS entity,
       esg.overall_score AS esg_score, esg.risk_level AS esg_risk
"""

PORTFOLIO_HOLDINGS_WITH_SECTORS = """
MATCH (p:Portfolio {portfolio_id: $portfolio_id})-[h:HOLDS]->(a:Asset)
WHERE ($as_of_date IS NULL OR h.as_of_date = $as_of_date)
OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:Sector)
RETURN a.name AS asset_name, a.isin AS isin, h.weight_pct AS weight_pct,
       h.as_of_date AS as_of_date,
       s.name AS sector, a.country AS country, a.asset_type AS asset_type
ORDER BY h.weight_pct DESC
"""

PORTFOLIO_NETWORK = """
MATCH (p:Portfolio {portfolio_id: $portfolio_id})-[r*1..2]-(connected)
WITH p, connected, [rel IN r | type(rel)] AS rel_types
RETURN DISTINCT labels(connected)[0] AS label,
       connected {.*} AS properties,
       rel_types
LIMIT 100
"""


# ============================================================
# PEER COMPARISON
# ============================================================

FIND_PEERS = """
MATCH (p:Portfolio {portfolio_id: $portfolio_id})-[:PEER_OF]-(peer:Portfolio)
RETURN peer.name AS peer_name, peer.portfolio_id AS peer_id,
       peer.aum AS aum, peer.morningstar_rating AS rating
ORDER BY peer.morningstar_rating DESC
"""

PEER_HOLDING_OVERLAP = """
MATCH (p1:Portfolio {portfolio_id: $portfolio_id})-[h1:HOLDS]->(a:Asset)<-[h2:HOLDS]-(p2:Portfolio)
WHERE p1 <> p2
  AND ($as_of_date IS NULL OR h1.as_of_date = $as_of_date)
  AND ($as_of_date IS NULL OR h2.as_of_date = $as_of_date)
WITH p2, COLLECT(a.name) AS shared_holdings, COUNT(a) AS overlap_count
RETURN p2.name AS peer, p2.portfolio_id AS peer_id,
       overlap_count, shared_holdings
ORDER BY overlap_count DESC
LIMIT 10
"""


# ============================================================
# ESG ANALYSIS
# ============================================================

ESG_CONTROVERSY_EXPOSURE = """
MATCH (p:Portfolio)-[h:HOLDS]->(a:Asset)-[:HAS_ESG_SCORE]->(esg:ESGRating)
WHERE esg.controversy_score <= $max_controversy
  AND ($as_of_date IS NULL OR h.as_of_date = $as_of_date)
WITH p, COLLECT(DISTINCT a.name) AS controversial_assets, COUNT(a) AS count
RETURN p.name AS portfolio, p.portfolio_id AS portfolio_id, count, controversial_assets
ORDER BY count DESC
"""

ESG_CROSS_PORTFOLIO_RISK = """
MATCH (a:Asset)-[:HAS_ESG_SCORE]->(esg:ESGRating)
WHERE esg.risk_level IN ['High', 'Severe']
WITH a, esg
MATCH (p:Portfolio)-[h:HOLDS]->(a)
WHERE ($as_of_date IS NULL OR h.as_of_date = $as_of_date)
WITH a.name AS asset, a.isin AS isin, esg.risk_level AS risk,
     COLLECT(DISTINCT p.name) AS exposed_portfolios
WHERE SIZE(exposed_portfolios) > 1
RETURN asset, isin, risk, exposed_portfolios, SIZE(exposed_portfolios) AS exposure_count
ORDER BY exposure_count DESC
"""

PORTFOLIO_ESG_VS_BENCHMARK = """
MATCH (p:Portfolio {portfolio_id: $portfolio_id})-[h:HOLDS]->(a:Asset)-[:HAS_ESG_SCORE]->(esg:ESGRating)
WHERE ($as_of_date IS NULL OR h.as_of_date = $as_of_date)
WITH p, AVG(esg.overall_score) AS portfolio_esg
MATCH (p)-[:TRACKS]->(b:Benchmark)-[c:COMPOSED_OF]->(ba:Asset)-[:HAS_ESG_SCORE]->(besg:ESGRating)
WHERE ($as_of_date IS NULL OR c.as_of_date = $as_of_date)
WITH p, portfolio_esg, b, AVG(besg.overall_score) AS benchmark_esg
RETURN p.name AS portfolio, portfolio_esg,
       b.name AS benchmark, benchmark_esg,
       portfolio_esg - benchmark_esg AS esg_differential
"""

EU_TAXONOMY_ALIGNMENT = """
MATCH (p:Portfolio)-[h:HOLDS]->(a:Asset)-[:HAS_ESG_SCORE]->(esg:ESGRating)
WHERE esg.taxonomy_alignment_pct IS NOT NULL
  AND ($as_of_date IS NULL OR h.as_of_date = $as_of_date)
WITH p, AVG(esg.taxonomy_alignment_pct) AS taxonomy_pct, AVG(esg.overall_score) AS esg_score
RETURN p.name AS portfolio, p.portfolio_id AS portfolio_id, taxonomy_pct, esg_score
ORDER BY taxonomy_pct DESC
"""


# ============================================================
# BENCHMARK ANALYSIS
# ============================================================

BENCHMARK_SECTOR_BREAKDOWN = """
MATCH (b:Benchmark {benchmark_id: $benchmark_id})-[c:COMPOSED_OF]->(a:Asset)-[:BELONGS_TO]->(s:Sector)
WITH s.name AS sector, SUM(c.weight_pct) AS total_weight, COUNT(a) AS count
RETURN sector, total_weight, count
ORDER BY total_weight DESC
"""

BENCHMARK_COMPOSITION_OVERLAP = """
MATCH (b1:Benchmark {benchmark_id: $benchmark_id_1})-[:COMPOSED_OF]->(a:Asset)<-[:COMPOSED_OF]-(b2:Benchmark {benchmark_id: $benchmark_id_2})
WITH COLLECT(a.name) AS shared, COUNT(a) AS overlap
RETURN shared, overlap
"""


# ============================================================
# CROSS-ENTITY & CONCENTRATION ANALYSIS
# ============================================================

CROSS_ENTITY_CONCENTRATION = """
MATCH (e:Entity)<-[:WORKS_FOR]-(fm:FundManager)<-[:MANAGED_BY]-(p:Portfolio)-[:HOLDS]->(a:Asset)
WITH a, COLLECT(DISTINCT e.name) AS entities, COLLECT(DISTINCT p.name) AS portfolios
WHERE SIZE(entities) > 1
RETURN a.name AS asset, a.isin AS isin, entities, portfolios,
       SIZE(entities) AS entity_count
ORDER BY entity_count DESC
LIMIT 20
"""

ENTITY_AUM_BREAKDOWN = """
MATCH (e:Entity)<-[:WORKS_FOR]-(fm:FundManager)<-[:MANAGED_BY]-(p:Portfolio)
WITH e.name AS entity, SUM(p.aum) AS total_aum, COUNT(p) AS fund_count,
     COLLECT(p.name) AS funds
RETURN entity, total_aum, fund_count, funds
ORDER BY total_aum DESC
"""


# ============================================================
# RELATIONSHIP DISCOVERY
# ============================================================

SHORTEST_PATH_BETWEEN_PORTFOLIOS = """
MATCH path = shortestPath(
    (p1:Portfolio {portfolio_id: $portfolio_id_1})-[*]-(p2:Portfolio {portfolio_id: $portfolio_id_2})
)
RETURN [n IN nodes(path) | {label: labels(n)[0], name: n.name}] AS nodes,
       [r IN relationships(path) | type(r)] AS relationships,
       length(path) AS path_length
"""

FUND_MANAGER_STYLE_SIMILARITY = """
MATCH (fm1:FundManager {manager_id: $manager_id})<-[:MANAGED_BY]-(p1:Portfolio)-[:HOLDS]->(a:Asset)<-[:HOLDS]-(p2:Portfolio)-[:MANAGED_BY]->(fm2:FundManager)
WHERE fm1 <> fm2
WITH fm2, COUNT(DISTINCT a) AS shared_holdings, COLLECT(DISTINCT a.name) AS common_assets
RETURN fm2.name AS similar_manager, fm2.manager_id AS manager_id,
       shared_holdings, common_assets[..5] AS top_common_assets
ORDER BY shared_holdings DESC
LIMIT 5
"""

# ============================================================
# GRAPH VISUALIZATION (returns nodes + edges for frontend)
# ============================================================

GRAPH_OVERVIEW = """
MATCH (n)
WITH labels(n)[0] AS label, COUNT(*) AS count
RETURN label, count
ORDER BY count DESC
"""

SUBGRAPH_AROUND_NODE = """
MATCH (center)-[r]-(neighbor)
WHERE id(center) = $node_id
RETURN center {.*, _label: labels(center)[0], _id: id(center)} AS source,
       type(r) AS relationship,
       neighbor {.*, _label: labels(neighbor)[0], _id: id(neighbor)} AS target
LIMIT 50
"""

INITIAL_GRAPH = """
MATCH (p:Portfolio)-[r:TRACKS]->(b:Benchmark)
RETURN p {.*, _label: 'Portfolio', _id: id(p)} AS source,
       type(r) AS relationship,
       b {.*, _label: 'Benchmark', _id: id(b)} AS target
"""

SEARCH_NODES = """
MATCH (n)
WHERE toLower(n.name) CONTAINS toLower($query)
RETURN id(n) AS id, labels(n)[0] AS label, n.name AS name
LIMIT 20
"""

# ============================================================
# VALUATION DATE DISCOVERY
# ============================================================

LIST_VALUATION_DATES = """
MATCH (p:Portfolio)
WHERE p.valuation_dates IS NOT NULL
UNWIND p.valuation_dates AS d
RETURN DISTINCT d AS valuation_date
ORDER BY valuation_date DESC
"""

# ============================================================
# PIPELINE RUN HISTORY
# ============================================================

CREATE_PIPELINE_RUN = """
CREATE (r:PipelineRun {
  run_id: $run_id,
  started_at: $started_at,
  completed_at: $completed_at,
  duration_seconds: $duration_seconds,
  status: $status,
  fetch_files: $fetch_files,
  fetch_records: $fetch_records,
  transform_etfs: $transform_etfs,
  transform_assets: $transform_assets,
  transform_holdings: $transform_holdings,
  validate_pass_rate: $validate_pass_rate,
  validate_warnings: $validate_warnings,
  validate_errors: $validate_errors,
  load_portfolios: $load_portfolios,
  load_assets: $load_assets,
  load_sectors: $load_sectors,
  load_holds: $load_holds,
  load_esg_ratings: $load_esg_ratings,
  valuation_date: $valuation_date,
  error_message: $error_message
})
RETURN r.run_id AS run_id
"""

LIST_PIPELINE_RUNS = """
MATCH (r:PipelineRun)
RETURN r {.*} AS run
ORDER BY r.started_at DESC
LIMIT 50
"""

GET_PIPELINE_RUN = """
MATCH (r:PipelineRun {run_id: $run_id})
RETURN r {.*} AS run
"""
