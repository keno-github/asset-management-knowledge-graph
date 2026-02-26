"""API request/response schemas.

These are separate from domain models — API contracts should not be
coupled to internal graph representations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortfolioSummary(BaseModel):
    portfolio_id: str
    name: str
    asset_class: str | None = None
    aum: float | None = None
    morningstar_rating: int | None = None
    benchmark: str | None = None


class PortfolioDetail(BaseModel):
    portfolio_id: str
    name: str
    asset_class: str | None = None
    aum: float | None = None
    morningstar_rating: int | None = None
    benchmark: str | None = None
    benchmark_id: str | None = None
    manager: str | None = None
    entity: str | None = None
    esg_score: float | None = None
    esg_risk: str | None = None


class HoldingResponse(BaseModel):
    asset_name: str
    isin: str | None = None
    weight_pct: float
    sector: str | None = None
    country: str | None = None
    asset_type: str | None = None


class PeerResponse(BaseModel):
    peer_name: str
    peer_id: str
    aum: float | None = None
    rating: int | None = None


class PeerOverlapResponse(BaseModel):
    peer: str
    peer_id: str
    overlap_count: int
    shared_holdings: list[str]


class ESGControversyResponse(BaseModel):
    portfolio: str
    portfolio_id: str
    count: int
    controversial_assets: list[str]


class ESGCrossPortfolioRisk(BaseModel):
    asset: str
    isin: str | None = None
    risk: str
    exposed_portfolios: list[str]
    exposure_count: int


class TaxonomyAlignment(BaseModel):
    portfolio: str
    portfolio_id: str
    taxonomy_pct: float
    esg_score: float


class GraphStats(BaseModel):
    nodes: dict[str, int]
    relationships: dict[str, int]


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["Which portfolios have the highest ESG risk?"],
    )


class ChatResponse(BaseModel):
    question: str
    cypher_query: str
    raw_results: list[dict]
    answer: str
    confidence: float = Field(ge=0, le=1)


class HealthResponse(BaseModel):
    status: str
    neo4j_connected: bool
    version: str
