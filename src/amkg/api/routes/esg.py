"""ESG analysis API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from amkg.api.deps import Neo4jDep
from amkg.api.schemas import (
    ESGControversyResponse,
    ESGCrossPortfolioRisk,
    TaxonomyAlignment,
)
from amkg.graph import queries as q

router = APIRouter()


@router.get("/controversy", response_model=list[ESGControversyResponse])
def esg_controversy_exposure(
    neo4j: Neo4jDep, max_controversy: int = 2
) -> list[dict]:
    """Portfolios exposed to controversial assets (low controversy score)."""
    return neo4j.run_query(
        q.ESG_CONTROVERSY_EXPOSURE, {"max_controversy": max_controversy}
    )


@router.get("/cross-portfolio-risk", response_model=list[ESGCrossPortfolioRisk])
def esg_cross_portfolio_risk(neo4j: Neo4jDep) -> list[dict]:
    """High-risk assets shared across multiple portfolios."""
    return neo4j.run_query(q.ESG_CROSS_PORTFOLIO_RISK)


@router.get("/taxonomy-alignment", response_model=list[TaxonomyAlignment])
def eu_taxonomy_alignment(neo4j: Neo4jDep) -> list[dict]:
    """EU Taxonomy alignment across portfolios."""
    return neo4j.run_query(q.EU_TAXONOMY_ALIGNMENT)
