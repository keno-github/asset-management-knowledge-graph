"""Natural language chat endpoint — the killer feature.

Users ask questions in plain English, and the LLM translates them to Cypher
queries, executes against Neo4j, and returns formatted answers.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from amkg.api.deps import Neo4jDep
from amkg.api.schemas import ChatRequest, ChatResponse
from amkg.config import settings
from amkg.llm.cypher_agent import CypherAgent

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, neo4j: Neo4jDep) -> dict:
    """Ask a natural language question about the knowledge graph.

    The LLM translates the question to Cypher, executes it against Neo4j,
    and formats a human-readable answer with the generated query shown
    for transparency.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured. Set it in .env to enable chat.",
        )

    try:
        agent = CypherAgent(neo4j_client=neo4j)
        return agent.answer(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
