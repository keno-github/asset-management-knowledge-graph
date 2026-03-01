"""Portfolio API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from amkg.api.deps import Neo4jDep
from amkg.api.schemas import (
    HoldingResponse,
    PeerOverlapResponse,
    PeerResponse,
    PortfolioDetail,
    PortfolioSummary,
)
from amkg.graph import queries as q

router = APIRouter()


@router.get("/", response_model=list[PortfolioSummary])
def list_portfolios(neo4j: Neo4jDep) -> list[dict]:
    """List all portfolios with summary info."""
    return neo4j.run_query(q.LIST_PORTFOLIOS)


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(portfolio_id: str, neo4j: Neo4jDep) -> dict:
    """Full portfolio profile with benchmark, manager, and ESG data."""
    try:
        results = neo4j.run_query(q.PORTFOLIO_FULL_PROFILE, {"portfolio_id": portfolio_id})
        if not results:
            raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
        return results[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {e}") from e


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingResponse])
def get_holdings(portfolio_id: str, neo4j: Neo4jDep) -> list[dict]:
    """Portfolio holdings with sector classifications."""
    return neo4j.run_query(
        q.PORTFOLIO_HOLDINGS_WITH_SECTORS, {"portfolio_id": portfolio_id}
    )


@router.get("/{portfolio_id}/peers", response_model=list[PeerResponse])
def get_peers(portfolio_id: str, neo4j: Neo4jDep) -> list[dict]:
    """Find peer portfolios (same Morningstar category)."""
    return neo4j.run_query(q.FIND_PEERS, {"portfolio_id": portfolio_id})


@router.get("/{portfolio_id}/peer-overlap", response_model=list[PeerOverlapResponse])
def get_peer_overlap(portfolio_id: str, neo4j: Neo4jDep) -> list[dict]:
    """Portfolios with overlapping holdings."""
    return neo4j.run_query(q.PEER_HOLDING_OVERLAP, {"portfolio_id": portfolio_id})
