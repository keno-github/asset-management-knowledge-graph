"""Two-step LLM agent: natural language -> Cypher -> execute -> format answer.

This is the killer feature. Users ask questions in plain English, and the
agent translates them to Cypher queries, executes against Neo4j, and
returns formatted answers with evidence.

Uses the Anthropic Claude API for both generation steps.
"""

from __future__ import annotations

from anthropic import Anthropic
from loguru import logger

from amkg.config import settings
from amkg.graph.client import Neo4jClient
from amkg.llm.guardrails import validate_cypher
from amkg.llm.prompts import ANSWER_FORMATTING_PROMPT, CYPHER_GENERATION_PROMPT, SCHEMA_CONTEXT


class CypherAgent:
    """Translates natural language questions into Cypher queries and answers.

    Two-step process:
    1. LLM generates a Cypher query from the natural language question
    2. Query executes against Neo4j
    3. LLM formats results into a human-readable answer
    """

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        self.neo4j = neo4j_client
        self.anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    def _generate_cypher(self, question: str) -> str:
        """Step 1: Generate Cypher from natural language."""
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": CYPHER_GENERATION_PROMPT.format(
                        schema_context=SCHEMA_CONTEXT, question=question
                    ),
                }
            ],
        )
        cypher = response.content[0].text.strip()

        # Strip markdown code fences if the model wraps them
        if cypher.startswith("```"):
            lines = cypher.split("\n")
            cypher = "\n".join(lines[1:])
            if cypher.endswith("```"):
                cypher = cypher[:-3]
            cypher = cypher.strip()

        return cypher

    def _format_answer(self, question: str, cypher: str, results: list[dict]) -> str:
        """Step 3: Format raw results into a human-readable answer."""
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": ANSWER_FORMATTING_PROMPT.format(
                        question=question,
                        cypher=cypher,
                        results=str(results[:25]),
                    ),
                }
            ],
        )
        return response.content[0].text.strip()

    def answer(self, question: str) -> dict:
        """Full pipeline: question -> cypher -> execute -> answer.

        Returns:
            Dict with question, cypher_query, raw_results, answer, confidence.
        """
        logger.info(f"[CypherAgent] Question: {question}")

        # Step 1: Generate Cypher
        cypher = self._generate_cypher(question)
        logger.info(f"[CypherAgent] Generated Cypher: {cypher}")

        # Step 2: Validate (read-only enforcement)
        validate_cypher(cypher)

        # Step 3: Execute against Neo4j
        try:
            results = self.neo4j.run_query(cypher)
        except Exception as e:
            logger.error(f"[CypherAgent] Query execution failed: {e}")
            return {
                "question": question,
                "cypher_query": cypher,
                "raw_results": [],
                "answer": (
                    f"The generated query failed to execute: {e}. "
                    "Try rephrasing your question."
                ),
                "confidence": 0.1,
            }

        # Step 4: Format answer
        answer = self._format_answer(question, cypher, results)
        logger.info(f"[CypherAgent] Answer generated ({len(results)} results)")

        return {
            "question": question,
            "cypher_query": cypher,
            "raw_results": results[:25],
            "answer": answer,
            "confidence": 0.85 if results else 0.3,
        }
