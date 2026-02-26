"""Unit tests for Cypher safety guardrails."""

import pytest

from amkg.llm.guardrails import validate_cypher


class TestCypherGuardrails:
    def test_valid_read_query(self) -> None:
        validate_cypher("MATCH (p:Portfolio) RETURN p.name LIMIT 10")

    def test_valid_complex_read(self) -> None:
        validate_cypher(
            "MATCH (p:Portfolio)-[:HOLDS]->(a:Asset) "
            "WITH p, COUNT(a) AS holdings "
            "RETURN p.name, holdings ORDER BY holdings DESC"
        )

    def test_blocks_create(self) -> None:
        with pytest.raises(ValueError, match="CREATE"):
            validate_cypher("CREATE (n:Portfolio {name: 'Evil'})")

    def test_blocks_merge(self) -> None:
        with pytest.raises(ValueError, match="MERGE"):
            validate_cypher("MERGE (n:Portfolio {name: 'Injected'})")

    def test_blocks_set(self) -> None:
        with pytest.raises(ValueError, match="SET"):
            validate_cypher("MATCH (n:Portfolio) SET n.name = 'Hacked'")

    def test_blocks_delete(self) -> None:
        with pytest.raises(ValueError, match="DELETE"):
            validate_cypher("MATCH (n) DELETE n")

    def test_blocks_detach_delete(self) -> None:
        with pytest.raises(ValueError, match="DELETE"):
            validate_cypher("MATCH (n) DETACH DELETE n")

    def test_blocks_remove(self) -> None:
        with pytest.raises(ValueError, match="REMOVE"):
            validate_cypher("MATCH (n:Portfolio) REMOVE n.name")

    def test_blocks_drop(self) -> None:
        with pytest.raises(ValueError, match="DROP"):
            validate_cypher("DROP INDEX ON :Portfolio(name)")

    def test_blocks_call(self) -> None:
        with pytest.raises(ValueError, match="CALL"):
            validate_cypher("CALL db.labels()")

    def test_blocks_load_csv(self) -> None:
        with pytest.raises(ValueError, match="LOAD CSV"):
            validate_cypher("LOAD CSV FROM 'file:///evil.csv' AS row")

    def test_blocks_foreach(self) -> None:
        with pytest.raises(ValueError, match="FOREACH"):
            validate_cypher("FOREACH (x IN [1,2,3] | noop)")

    def test_blocks_apoc(self) -> None:
        with pytest.raises(ValueError, match="APOC"):
            validate_cypher("MATCH (n) RETURN apoc.convert.toJson(n)")

    def test_case_insensitive(self) -> None:
        with pytest.raises(ValueError, match="CREATE"):
            validate_cypher("create (n:Portfolio)")

    def test_keyword_in_string_not_blocked(self) -> None:
        # "SET" inside a property value should not trigger (it's in a WHERE clause)
        validate_cypher(
            "MATCH (p:Portfolio) WHERE p.name CONTAINS 'ASSET' RETURN p"
        )
