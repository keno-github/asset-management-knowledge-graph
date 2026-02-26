"""Relationship models representing edges in the knowledge graph.

Each class defines the properties stored on a Neo4j relationship. The class
name maps to the relationship type (e.g., Tracks -> :TRACKS).
"""

from datetime import date

from pydantic import BaseModel, Field


class Tracks(BaseModel):
    """Portfolio -[:TRACKS]-> Benchmark.

    A portfolio's benchmark assignment. Most funds have one primary benchmark
    but may have secondary benchmarks for different reporting contexts.
    """

    is_primary: bool = Field(default=True, description="Primary vs secondary benchmark")
    effective_date: date | None = None


class Holds(BaseModel):
    """Portfolio -[:HOLDS]-> Asset.

    Position-level data from IBOR. Weight and market value as of a specific date.
    """

    weight_pct: float = Field(..., ge=0, le=100)
    market_value: float | None = Field(None, ge=0)
    as_of_date: date


class BelongsTo(BaseModel):
    """Asset -[:BELONGS_TO]-> Sector.

    GICS or ICB classification. Assets may be reclassified during annual reviews.
    """

    classification_system: str = "GICS"


class HasPerformance(BaseModel):
    """Portfolio|Benchmark -[:HAS_PERFORMANCE]-> PerformanceRecord."""

    period_type: str = Field(..., description="MTD, QTD, YTD, 1Y, 3Y, 5Y, SI")


class MeasuredAgainst(BaseModel):
    """PerformanceRecord -[:MEASURED_AGAINST]-> Benchmark.

    Links a performance record to the benchmark used for relative measurement.
    """

    excess_return_pct: float | None = Field(None, description="Active return vs benchmark")


class HasESGScore(BaseModel):
    """Portfolio|Asset -[:HAS_ESG_SCORE]-> ESGRating."""

    rating_date: date


class RatedBy(BaseModel):
    """ESGRating -[:RATED_BY]-> RatingProvider."""

    methodology: str | None = None


class ManagedBy(BaseModel):
    """Portfolio -[:MANAGED_BY]-> FundManager."""

    role: str = Field(default="Lead Manager")
    start_date: date | None = None


class WorksFor(BaseModel):
    """FundManager -[:WORKS_FOR]-> Entity."""

    department: str | None = None


class ComposedOf(BaseModel):
    """Benchmark -[:COMPOSED_OF]-> Asset.

    Index constituent with weight. Changes during rebalancing events.
    """

    weight_pct: float = Field(..., ge=0, le=100)
    as_of_date: date


class PeerOf(BaseModel):
    """Portfolio -[:PEER_OF]-> Portfolio.

    Bidirectional peer relationship based on Morningstar category.
    """

    category: str
    as_of_date: date


class ParentOf(BaseModel):
    """Entity -[:PARENT_OF]-> Entity.

    Corporate hierarchy from GLEIF LEI database.
    """

    ownership_pct: float | None = Field(None, ge=0, le=100)
