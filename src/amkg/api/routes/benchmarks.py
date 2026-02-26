"""Benchmark API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from amkg.api.deps import Neo4jDep
from amkg.graph import queries as q

router = APIRouter()


@router.get("/{benchmark_id}/sectors")
def benchmark_sector_breakdown(benchmark_id: str, neo4j: Neo4jDep) -> list[dict]:
    """Sector breakdown for a benchmark's composition."""
    return neo4j.run_query(
        q.BENCHMARK_SECTOR_BREAKDOWN, {"benchmark_id": benchmark_id}
    )


@router.get("/overlap")
def benchmark_overlap(
    benchmark_id_1: str, benchmark_id_2: str, neo4j: Neo4jDep
) -> list[dict]:
    """Constituent overlap between two benchmarks."""
    return neo4j.run_query(
        q.BENCHMARK_COMPOSITION_OVERLAP,
        {"benchmark_id_1": benchmark_id_1, "benchmark_id_2": benchmark_id_2},
    )
