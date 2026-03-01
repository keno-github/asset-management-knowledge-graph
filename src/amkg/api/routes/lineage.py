"""Data lineage and provenance API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from amkg.api.deps import Neo4jDep

router = APIRouter()

# Map node labels to their primary key field
_LABEL_TO_ID_FIELD: dict[str, str] = {
    "Portfolio": "portfolio_id",
    "Asset": "isin",
    "Benchmark": "benchmark_id",
    "Sector": "sector_id",
    "ESGRating": "rating_id",
}


class LineageResponse(BaseModel):
    node_label: str
    node_id: str
    source: str | None = None
    ingested_at: str | None = None
    pipeline_run_id: str | None = None


@router.get(
    "/{node_label}/{node_id}",
    response_model=LineageResponse,
    summary="Get data provenance for a node",
)
def get_node_lineage(node_label: str, node_id: str, neo4j: Neo4jDep) -> dict:
    """Return data provenance metadata for a specific node.

    - **node_label**: Portfolio, Asset, Benchmark, Sector, or ESGRating
    - **node_id**: the primary key value (portfolio_id, ISIN, benchmark_id, etc.)
    """
    id_field = _LABEL_TO_ID_FIELD.get(node_label)
    if not id_field:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown node label '{node_label}'. "
            f"Valid labels: {list(_LABEL_TO_ID_FIELD.keys())}",
        )

    # Safe: node_label and id_field are validated against the allowlist above
    query = f"""
    MATCH (n:{node_label} {{{id_field}: $node_id}})
    RETURN labels(n)[0] AS node_label,
           n.{id_field} AS node_id,
           n._source AS source,
           n._ingested_at AS ingested_at,
           n._pipeline_run_id AS pipeline_run_id
    LIMIT 1
    """
    results = neo4j.run_query(query, {"node_id": node_id})
    if not results:
        raise HTTPException(
            status_code=404, detail=f"{node_label} '{node_id}' not found"
        )
    return results[0]
