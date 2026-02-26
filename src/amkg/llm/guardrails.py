"""Safety validation for LLM-generated Cypher queries.

Ensures that no write operations can be executed through the
natural language interface. This is a critical security boundary.
"""

from __future__ import annotations

import re

FORBIDDEN_KEYWORDS = [
    "CREATE",
    "MERGE",
    "SET",
    "DELETE",
    "REMOVE",
    "DROP",
    "CALL",
    "LOAD CSV",
    "FOREACH",
]


def validate_cypher(cypher: str) -> None:
    """Reject any Cypher query containing write operations.

    Args:
        cypher: The generated Cypher query string.

    Raises:
        ValueError: If the query contains forbidden write operations.
    """
    upper = cypher.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            raise ValueError(
                f"Generated Cypher contains forbidden operation: '{keyword}'. "
                "Only read-only queries (MATCH, RETURN, WITH, WHERE) are allowed."
            )

    # Check for suspicious patterns
    if "apoc." in cypher.lower():
        raise ValueError("APOC procedures are not allowed in generated queries.")
