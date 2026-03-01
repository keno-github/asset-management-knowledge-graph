"""OWL-RL reasoning over the AMKG ontology and live graph data.

Demonstrates formal inference by:
1. Exporting Neo4j data to RDF
2. Merging with the OWL ontology (amkg.ttl)
3. Running OWL-RL deductive closure
4. Diffing to find inferred triples
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import owlrl
from loguru import logger

from amkg.graph.client import Neo4jClient
from amkg.rdf.exporter import AMKG, neo4j_to_rdf

# Path to ontology file
_ONTOLOGY_PATH = Path(__file__).resolve().parents[3] / "data" / "ontology" / "amkg.ttl"

# Prefix map for readable triple output
_PREFIX_MAP: dict[str, str] = {
    "https://w3id.org/amkg/ontology#": "amkg:",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    "http://www.w3.org/2002/07/owl#": "owl:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
    "http://schema.org/": "schema:",
}


def _shorten_uri(uri: Any) -> str:
    """Shorten a URI using known prefixes for display."""
    uri_str = str(uri)
    for full, prefix in _PREFIX_MAP.items():
        if uri_str.startswith(full):
            return prefix + uri_str[len(full):]
    return uri_str


def _triple_to_readable(s: Any, p: Any, o: Any) -> dict[str, str]:
    """Convert a triple to a human-readable dict."""
    return {
        "subject": _shorten_uri(s),
        "predicate": _shorten_uri(p),
        "object": _shorten_uri(o),
    }


def run_reasoning(client: Neo4jClient) -> dict[str, Any]:
    """Run OWL-RL reasoning and return explicit vs inferred triples.

    Args:
        client: Active Neo4j client.

    Returns:
        Dict with triple counts and categorized inferred triples.
    """
    # Step 1: Export live data to RDF
    g = neo4j_to_rdf(client)
    explicit_count = len(g)
    logger.info(f"[Reasoner] Exported {explicit_count} explicit triples from Neo4j")

    # Step 2: Merge ontology
    if _ONTOLOGY_PATH.exists():
        g.parse(str(_ONTOLOGY_PATH), format="turtle")
        after_ontology = len(g)
        logger.info(f"[Reasoner] After ontology merge: {after_ontology} triples")
    else:
        logger.warning(f"[Reasoner] Ontology not found at {_ONTOLOGY_PATH}")

    # Step 3: Snapshot existing triples
    existing_triples = set(g)

    # Step 4: Run OWL-RL deductive closure
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    total_count = len(g)
    logger.info(f"[Reasoner] After reasoning: {total_count} triples")

    # Step 5: Diff to find inferred triples
    inferred = set(g) - existing_triples

    # Step 6: Categorize inferred triples
    type_inheritance: list[dict[str, str]] = []
    domain_range: list[dict[str, str]] = []
    other: list[dict[str, str]] = []

    rdf_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    rdfs_subclass = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
    owl_thing = "http://www.w3.org/2002/07/owl#Thing"
    owl_named = "http://www.w3.org/2002/07/owl#NamedIndividual"
    schema_prefix = "http://schema.org/"

    for s, p, o in inferred:
        readable = _triple_to_readable(s, p, o)
        p_str = str(p)
        o_str = str(o)

        if (
            p_str == rdf_type
            and (o_str.startswith(schema_prefix) or o_str in (owl_thing, owl_named))
        ) or p_str == rdfs_subclass:
            type_inheritance.append(readable)
        elif p_str == rdf_type and str(AMKG) in o_str:
            domain_range.append(readable)
        else:
            other.append(readable)

    return {
        "explicit_triples": explicit_count,
        "total_triples": total_count,
        "inferred_triples": len(inferred),
        "categories": {
            "type_inheritance": {
                "description": (
                    "Types inferred through rdfs:subClassOf chains "
                    "(e.g., Portfolio → schema:InvestmentFund → schema:FinancialProduct)"
                ),
                "count": len(type_inheritance),
                "examples": type_inheritance[:10],
            },
            "domain_range_inference": {
                "description": (
                    "Types inferred from rdfs:domain and rdfs:range declarations "
                    "on object and datatype properties"
                ),
                "count": len(domain_range),
                "examples": domain_range[:10],
            },
            "other": {
                "description": "Other inferred triples (OWL axioms, equivalences, etc.)",
                "count": len(other),
                "examples": other[:10],
            },
        },
    }
