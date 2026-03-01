"""Ontology and schema documentation endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "ontology"


@router.get(
    "/ontology.ttl",
    summary="Download OWL/RDF ontology in Turtle format",
)
def get_ontology_ttl() -> FileResponse:
    """Serve the formal OWL ontology file describing the AMKG schema."""
    path = ONTOLOGY_DIR / "amkg.ttl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Ontology file not found")
    return FileResponse(path=path, media_type="text/turtle", filename="amkg.ttl")


@router.get(
    "/ontology",
    summary="Ontology metadata summary",
)
def get_ontology_summary() -> dict:
    """Return a structured summary of the ontology for programmatic consumption."""
    return {
        "namespace": "https://w3id.org/amkg/ontology#",
        "version": "1.0.0",
        "format": "OWL 2 / Turtle",
        "classes": [
            {
                "name": "Portfolio",
                "uri": "amkg:Portfolio",
                "description": "An investment portfolio or ETF fund.",
            },
            {
                "name": "Asset",
                "uri": "amkg:Asset",
                "description": "A financial instrument identified by ISIN.",
            },
            {
                "name": "Benchmark",
                "uri": "amkg:Benchmark",
                "description": "A market index that portfolios track.",
            },
            {
                "name": "Sector",
                "uri": "amkg:Sector",
                "description": "A GICS industry sector classification.",
            },
            {
                "name": "ESGRating",
                "uri": "amkg:ESGRating",
                "description": "An ESG rating with E/S/G pillar scores.",
            },
        ],
        "object_properties": [
            {"name": "holds", "domain": "Portfolio", "range": "Asset"},
            {"name": "tracks", "domain": "Portfolio", "range": "Benchmark"},
            {"name": "belongsTo", "domain": "Asset", "range": "Sector"},
            {"name": "composedOf", "domain": "Benchmark", "range": "Asset"},
            {"name": "hasESGScore", "domain": "Asset", "range": "ESGRating"},
        ],
        "download_url": "/ontology.ttl",
    }


@router.get(
    "/ontology/versions",
    summary="Ontology version history",
)
def get_ontology_versions() -> dict:
    """Return the ontology changelog with version history.

    Demonstrates ontology governance and change management.
    """
    return {
        "current_version": "1.0.0",
        "versions": [
            {
                "version": "1.0.0",
                "date": "2025-03-01",
                "changes": [
                    "Initial formal OWL 2 ontology with 5 classes and 5 object properties",
                    "21 datatype properties with XSD-typed ranges",
                    "Lineage/provenance properties: source, ingestedAt, pipelineRunId",
                    "SKOS vocabulary integration via skosConceptUri linking",
                    "Schema.org alignment: Portfolio rdfs:subClassOf schema:InvestmentFund",
                ],
            },
            {
                "version": "0.2.0",
                "date": "2025-02-15",
                "changes": [
                    "Added ESGRating class with pillar scores and controversy tracking",
                    "Added hasESGScore object property (Asset -> ESGRating)",
                    "Added taxonomyAlignmentPct for EU Taxonomy alignment",
                ],
            },
            {
                "version": "0.1.0",
                "date": "2025-02-01",
                "changes": [
                    "Initial draft: Portfolio, Asset, Benchmark, Sector classes",
                    "Core relationships: holds, tracks, belongsTo, composedOf",
                    "Basic datatype properties for identification and classification",
                ],
            },
        ],
    }
