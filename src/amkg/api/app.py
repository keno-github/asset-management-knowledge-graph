"""FastAPI application factory with Neo4j lifecycle management.

Run with:
    uvicorn amkg.api.app:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from amkg import __version__
from amkg.api.routes import (
    benchmarks,
    chat,
    discovery,
    esg,
    ingest,
    lineage,
    ontology,
    portfolios,
    rdf,
    reasoning,
    vocabulary,
)
from amkg.api.schemas import GraphStats, HealthResponse
from amkg.config import settings
from amkg.graph.client import Neo4jClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage Neo4j connection lifecycle."""
    app.state.neo4j = Neo4jClient()
    yield
    app.state.neo4j.close()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Asset Management Knowledge Graph API",
        description=(
            "Graph-powered analytics for investment portfolios, "
            "ESG ratings, benchmarks, and relationship discovery. "
            "Built with Neo4j, FastAPI, and Claude AI."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    origins = (
        ["*"]
        if settings.CORS_ORIGINS == "*"
        else [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
    app.include_router(benchmarks.router, prefix="/api/benchmarks", tags=["Benchmarks"])
    app.include_router(esg.router, prefix="/api/esg", tags=["ESG"])
    app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(ontology.router, tags=["Schema"])
    app.include_router(lineage.router, prefix="/api/lineage", tags=["Lineage"])
    app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["Vocabulary"])
    app.include_router(rdf.router, prefix="/api/rdf", tags=["RDF"])
    app.include_router(reasoning.router, prefix="/api/rdf", tags=["RDF"])
    app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingest"])

    # Health and stats endpoints
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> dict:
        """Check API and Neo4j connectivity."""
        neo4j: Neo4jClient = app.state.neo4j
        connected = neo4j.verify_connectivity()
        return {
            "status": "healthy" if connected else "degraded",
            "neo4j_connected": connected,
            "version": __version__,
        }

    @app.get("/stats", response_model=GraphStats, tags=["System"])
    def graph_stats() -> dict:
        """Return node and relationship counts."""
        neo4j: Neo4jClient = app.state.neo4j
        return neo4j.get_stats()

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception on {request.url}: {exc}")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return app


app = create_app()
