"""FastAPI dependencies — Neo4j session management and authentication."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from amkg.config import settings
from amkg.graph.client import Neo4jClient


def get_neo4j(request: Request) -> Neo4jClient:
    """Inject the Neo4j client from application state."""
    return request.app.state.neo4j  # type: ignore[no-any-return]


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str | None:
    """Optional API key authentication.

    In development, requests without an API key are allowed.
    In production, set API_KEY to enforce authentication.
    """
    if settings.API_KEY == "dev-api-key-change-me":
        return x_api_key  # Dev mode: no enforcement

    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


Neo4jDep = Annotated[Neo4jClient, Depends(get_neo4j)]
