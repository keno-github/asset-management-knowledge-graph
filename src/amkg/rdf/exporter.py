"""Convert Neo4j graph data to RDF using rdflib.

Maps node labels to OWL classes and relationship types to object properties
using the AMKG ontology namespace (https://w3id.org/amkg/ontology#).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from amkg.graph.client import Neo4jClient

AMKG = Namespace("https://w3id.org/amkg/ontology#")

# Primary key field per node label
_PRIMARY_KEYS: dict[str, str] = {
    "Portfolio": "portfolio_id",
    "Asset": "isin",
    "Benchmark": "benchmark_id",
    "Sector": "sector_id",
    "ESGRating": "rating_id",
}

# Neo4j relationship type -> ontology object property
_REL_MAP: dict[str, str] = {
    "HOLDS": "holds",
    "TRACKS": "tracks",
    "BELONGS_TO": "belongsTo",
    "COMPOSED_OF": "composedOf",
    "HAS_ESG_SCORE": "hasESGScore",
}

# Neo4j property name (snake_case) -> ontology datatype property (camelCase)
_PROP_MAP: dict[str, str] = {
    "portfolio_id": "portfolioId",
    "name": "name",
    "isin": "isin",
    "asset_class": "assetClass",
    "currency": "currency",
    "aum": "aum",
    "as_of_date": "asOfDate",
    "is_active": "isActive",
    "domicile": "domicile",
    "ticker": "ticker",
    "asset_type": "assetType",
    "country": "country",
    "exchange": "exchange",
    "market_cap": "marketCap",
    "sector": "sector",
    "industry": "industry",
    "benchmark_id": "benchmarkId",
    "provider": "provider",
    "region": "region",
    "sector_id": "sectorId",
    "classification_system": "classificationSystem",
    "level": "level",
    "skos_concept_uri": "skosConceptUri",
    "rating_id": "ratingId",
    "overall_score": "overallScore",
    "environmental_score": "environmentalScore",
    "social_score": "socialScore",
    "governance_score": "governanceScore",
    "risk_level": "riskLevel",
    "taxonomy_alignment_pct": "taxonomyAlignmentPct",
    "controversy_score": "controversyScore",
    "rating_date": "ratingDate",
    "_source": "source",
    "_ingested_at": "ingestedAt",
    "_pipeline_run_id": "pipelineRunId",
}

# XSD type hints for known numeric/boolean/date properties
_XSD_TYPES: dict[str, URIRef] = {
    "aum": XSD.decimal,
    "market_cap": XSD.decimal,
    "overall_score": XSD.decimal,
    "environmental_score": XSD.decimal,
    "social_score": XSD.decimal,
    "governance_score": XSD.decimal,
    "taxonomy_alignment_pct": XSD.decimal,
    "controversy_score": XSD.integer,
    "level": XSD.integer,
    "is_active": XSD.boolean,
    "as_of_date": XSD.date,
    "rating_date": XSD.date,
    "_ingested_at": XSD.dateTime,
}

VALID_LABELS = set(_PRIMARY_KEYS.keys())


def _node_uri(label: str, props: dict[str, Any]) -> URIRef | None:
    """Build a URI for a Neo4j node using its label and primary key."""
    pk_field = _PRIMARY_KEYS.get(label)
    if not pk_field:
        return None
    pk_value = props.get(pk_field)
    if pk_value is None:
        return None
    # Percent-encode characters that are illegal in URI local names
    safe_id = quote(str(pk_value), safe="-._~")
    return AMKG[f"{label}_{safe_id}"]


def _literal(key: str, value: Any) -> Literal:
    """Create a typed RDF literal for a property value."""
    xsd_type = _XSD_TYPES.get(key)
    if xsd_type:
        # Ensure temporal/complex types are stringified for rdflib compatibility
        if xsd_type in (XSD.date, XSD.dateTime):
            return Literal(str(value), datatype=xsd_type)
        return Literal(value, datatype=xsd_type)
    return Literal(str(value))


def neo4j_to_rdf(client: Neo4jClient, label: str | None = None) -> Graph:
    """Export Neo4j graph data as an rdflib Graph.

    Args:
        client: Active Neo4j client.
        label: Optional node label filter (e.g. "Portfolio"). If None, exports all.

    Returns:
        An rdflib.Graph populated with triples.
    """
    g = Graph()
    g.bind("amkg", AMKG)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)

    # Query nodes
    if label and label in VALID_LABELS:
        node_query = f"MATCH (n:{label}) RETURN n, labels(n)[0] AS label, elementId(n) AS eid"
    else:
        node_query = "MATCH (n) RETURN n, labels(n)[0] AS label, elementId(n) AS eid"

    nodes = client.run_query(node_query)
    eid_to_uri: dict[str, URIRef] = {}

    for record in nodes:
        node_label = record["label"]
        props = record["n"]
        eid = record["eid"]

        uri = _node_uri(node_label, props)
        if uri is None:
            continue

        eid_to_uri[eid] = uri

        # rdf:type
        class_uri = AMKG[node_label]
        g.add((uri, RDF.type, class_uri))

        # Datatype properties
        for key, value in props.items():
            if value is None:
                continue
            onto_prop = _PROP_MAP.get(key)
            if onto_prop:
                g.add((uri, AMKG[onto_prop], _literal(key, value)))

    # Query relationships
    if label and label in VALID_LABELS:
        rel_query = (
            f"MATCH (a:{label})-[r]->(b) "
            "RETURN elementId(a) AS src, type(r) AS rtype, elementId(b) AS tgt"
        )
    else:
        rel_query = (
            "MATCH (a)-[r]->(b) "
            "RETURN elementId(a) AS src, type(r) AS rtype, elementId(b) AS tgt"
        )

    rels = client.run_query(rel_query)

    for record in rels:
        src_uri = eid_to_uri.get(record["src"])
        tgt_uri = eid_to_uri.get(record["tgt"])
        rtype = record["rtype"]

        if not src_uri or not tgt_uri:
            continue

        onto_rel = _REL_MAP.get(rtype)
        if onto_rel:
            g.add((src_uri, AMKG[onto_rel], tgt_uri))

    return g
