"""Relationship discovery API endpoints — the graph advantage."""

from __future__ import annotations

from fastapi import APIRouter, Query

from amkg.api.deps import Neo4jDep
from amkg.graph import queries as q

router = APIRouter()


@router.get("/shortest-path")
def shortest_path(
    portfolio_id_1: str, portfolio_id_2: str, neo4j: Neo4jDep
) -> list[dict]:
    """Find shortest path between two portfolios in the graph."""
    return neo4j.run_query(
        q.SHORTEST_PATH_BETWEEN_PORTFOLIOS,
        {"portfolio_id_1": portfolio_id_1, "portfolio_id_2": portfolio_id_2},
    )


@router.get("/cross-entity-concentration")
def cross_entity_concentration(neo4j: Neo4jDep) -> list[dict]:
    """Assets held across multiple corporate entities."""
    return neo4j.run_query(q.CROSS_ENTITY_CONCENTRATION)


@router.get("/entity-aum")
def entity_aum_breakdown(neo4j: Neo4jDep) -> list[dict]:
    """AUM breakdown by entity."""
    return neo4j.run_query(q.ENTITY_AUM_BREAKDOWN)


@router.get("/manager-similarity/{manager_id}")
def fund_manager_similarity(manager_id: str, neo4j: Neo4jDep) -> list[dict]:
    """Find fund managers with similar holding patterns."""
    return neo4j.run_query(
        q.FUND_MANAGER_STYLE_SIMILARITY, {"manager_id": manager_id}
    )


@router.get("/graph-overview")
def graph_overview(neo4j: Neo4jDep) -> list[dict]:
    """Node counts by label — overview of the knowledge graph."""
    return neo4j.run_query(q.GRAPH_OVERVIEW)


@router.get("/subgraph/{node_id}")
def subgraph(node_id: int, neo4j: Neo4jDep) -> list[dict]:
    """Get the immediate neighborhood of a node (for visualization)."""
    return neo4j.run_query(q.SUBGRAPH_AROUND_NODE, {"node_id": node_id})


@router.get("/initial-graph")
def initial_graph(neo4j: Neo4jDep) -> list[dict]:
    """Starting graph view — all portfolios with their benchmarks."""
    return neo4j.run_query(q.INITIAL_GRAPH)


@router.get("/search-nodes")
def search_nodes(neo4j: Neo4jDep, search: str = Query(alias="q")) -> list[dict]:
    """Search nodes by name across all types."""
    return neo4j.run_query(q.SEARCH_NODES, {"query": search})
