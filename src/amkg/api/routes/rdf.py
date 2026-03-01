"""RDF export and SPARQL query endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from amkg.api.deps import Neo4jDep
from amkg.rdf.exporter import AMKG, VALID_LABELS, neo4j_to_rdf

router = APIRouter()

_FORMAT_MAP: dict[str, tuple[str, str]] = {
    "turtle": ("turtle", "text/turtle"),
    "json-ld": ("json-ld", "application/ld+json"),
    "n-triples": ("nt", "application/n-triples"),
    "xml": ("xml", "application/rdf+xml"),
}

# Auto-injected into every SPARQL query so users don't need to type PREFIX declarations
_SPARQL_PREAMBLE = f"PREFIX amkg: <{AMKG}>\n"

_SPARQL_WRITE_KEYWORDS = frozenset(
    ("INSERT", "DELETE", "LOAD", "CLEAR", "DROP", "CREATE", "COPY", "MOVE", "ADD")
)


@router.get("/formats", summary="List supported RDF serialization formats")
def list_formats() -> list[dict[str, str]]:
    """Return the available RDF export formats."""
    return [
        {"id": k, "media_type": v[1]}
        for k, v in _FORMAT_MAP.items()
    ]


@router.get("/export", summary="Export graph data as RDF")
def export_rdf(
    neo4j: Neo4jDep,
    output_format: str = Query("turtle", alias="format", description="Serialization format"),
    label: str | None = Query(None, description="Filter by node label"),
) -> Response:
    """Export Neo4j graph data as RDF triples.

    Converts nodes and relationships into RDF using the AMKG ontology namespace.
    Supports multiple serialization formats via the `format` query parameter.
    """
    if output_format not in _FORMAT_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{output_format}'. Choose from: {', '.join(_FORMAT_MAP)}",
        )

    if label and label not in VALID_LABELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid label '{label}'. Choose from: {', '.join(sorted(VALID_LABELS))}",
        )

    g = neo4j_to_rdf(neo4j, label=label)
    rdflib_format, media_type = _FORMAT_MAP[output_format]
    serialized = g.serialize(format=rdflib_format)

    return Response(content=serialized, media_type=media_type)


@router.get("/sparql", summary="Execute a SPARQL query against the graph")
def sparql_query(
    neo4j: Neo4jDep,
    query: str = Query(..., description="SPARQL query string"),
) -> dict[str, Any]:
    """Execute a SPARQL SELECT or ASK query against an in-memory RDF export.

    Loads the full graph into rdflib, then evaluates the SPARQL query.
    The AMKG namespace prefix is auto-injected so queries can use `amkg:` directly.
    Returns structured JSON results with column names and rows.
    """
    # Block SPARQL Update operations
    stripped = query.strip()
    first_word = stripped.split()[0].upper() if stripped else ""
    if first_word in _SPARQL_WRITE_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail="Only SELECT, ASK, and CONSTRUCT queries are supported.",
        )

    # Auto-inject AMKG prefix if not already declared
    if "PREFIX amkg:" not in query and "prefix amkg:" not in query:
        query = _SPARQL_PREAMBLE + query

    g = neo4j_to_rdf(neo4j)

    try:
        results = g.query(query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SPARQL error: {e}") from e

    # ASK query -> boolean
    ask_answer = getattr(results, "askAnswer", None)
    if isinstance(ask_answer, bool):
        return {"type": "ask", "result": ask_answer}

    # CONSTRUCT query -> return as turtle
    result_graph = getattr(results, "graph", None)
    if result_graph is not None and len(result_graph) > 0:
        return {"type": "construct", "turtle": result_graph.serialize(format="turtle")}

    # SELECT query -> tabular
    columns = [str(v) for v in results.vars] if results.vars else []
    rows: list[dict[str, str]] = []
    for row in results:
        rows.append({
            col: str(row[i]) if row[i] is not None else ""
            for i, col in enumerate(columns)
        })

    return {"type": "select", "columns": columns, "rows": rows}
