"""OWL-RL reasoning endpoint — demonstrates formal inference over the knowledge graph."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from amkg.api.deps import Neo4jDep
from amkg.rdf.reasoner import run_reasoning

router = APIRouter()


@router.get("/reasoning")
def get_reasoning(neo4j: Neo4jDep) -> dict[str, Any]:
    """Run OWL-RL reasoning over the live graph + ontology.

    Returns explicit triple count, inferred triple count, and
    categorized examples of inferred knowledge.
    """
    try:
        return run_reasoning(neo4j)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reasoning failed: {e}",
        ) from e
