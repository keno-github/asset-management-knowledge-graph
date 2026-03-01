"""Node models representing core asset management domain concepts.

Each class maps to a Neo4j node label. Properties are validated via Pydantic
before being written to the graph, ensuring data quality at the boundary.

Domain sources:
    - IBOR systems (portfolios, holdings)
    - Security master data (assets)
    - Bloomberg, MSCI, Morningstar (benchmarks, ratings)
    - GICS taxonomy (sectors)
    - MSCI ESG, Sustainalytics (ESG ratings)
    - GLEIF (legal entities)
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from amkg.models.enums import AssetClass, AssetType, ESGRiskLevel, MorningstarRating


class Portfolio(BaseModel):
    """An investment portfolio or fund.

    Represents the 'book of record' from IBOR — the authoritative source
    of positions and transactions for a given fund.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    portfolio_id: str = Field(..., description="Internal portfolio identifier")
    name: str = Field(..., min_length=1)
    isin: str | None = Field(None, pattern=r"^[A-Z]{2}[A-Z0-9]{9}\d$", description="ISIN")
    asset_class: AssetClass
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    inception_date: date | None = None
    aum: float | None = Field(
        None, ge=0, description="Assets Under Management (sum of holding market values)"
    )
    morningstar_category: str | None = None
    morningstar_rating: MorningstarRating | None = None
    domicile: str | None = None
    as_of_date: date | None = Field(None, description="Holdings valuation date from data source")
    is_active: bool = True


class Benchmark(BaseModel):
    """A market index or composite used as a performance reference.

    Portfolios track benchmarks via the TRACKS relationship. Benchmark
    composition changes during rebalancing events (quarterly for most indices).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    benchmark_id: str
    name: str = Field(..., min_length=1)
    ticker: str | None = None
    provider: str = Field(..., description="Index provider: MSCI, STOXX, Bloomberg, S&P")
    asset_class: AssetClass
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    region: str | None = None


class Asset(BaseModel):
    """An individual financial security (equity, bond, etc.).

    The fundamental building block of portfolios and benchmarks. Linked
    to sectors via BELONGS_TO and to ESG ratings via HAS_ESG_SCORE.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    isin: str = Field(
        ..., pattern=r"^[A-Z]{2}[A-Z0-9]{10}$", description="ISIN or synthetic identifier"
    )
    name: str = Field(..., min_length=1)
    ticker: str | None = None
    asset_type: AssetType = AssetType.COMMON_STOCK
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    country: str | None = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    exchange: str | None = None
    market_cap: float | None = Field(None, ge=0, description="Market cap in millions USD")
    sector: str | None = None
    industry: str | None = None


class Sector(BaseModel):
    """Industry/sector classification under GICS or ICB taxonomy.

    GICS has 4 levels: Sector -> Industry Group -> Industry -> Sub-Industry.
    Assets are classified at the most granular available level.
    """

    sector_id: str
    name: str = Field(..., min_length=1)
    classification_system: str = Field(default="GICS")
    level: int = Field(default=1, ge=1, le=4, description="1=Sector, 4=Sub-Industry")
    parent_sector_id: str | None = None


class Holding(BaseModel):
    """A portfolio position — the bridge between Portfolio and Asset.

    Represents the IBOR position data: what a portfolio owns, how much,
    and as of what date. Weight percentages should sum to ~100% per portfolio.
    """

    portfolio_id: str
    isin: str = Field(..., description="Asset ISIN this holding refers to")
    weight_pct: float = Field(..., ge=0, le=100, description="Weight in portfolio as %")
    market_value: float | None = Field(None, ge=0, description="Market value in fund currency")
    as_of_date: date


class PerformanceRecord(BaseModel):
    """Return data for a portfolio or benchmark over a defined period.

    Computed from daily NAV data. Time-Weighted Return (TWR) is standard
    for fund performance measurement per GIPS compliance.
    """

    record_id: str
    entity_id: str = Field(..., description="portfolio_id or benchmark_id this record belongs to")
    entity_type: str = Field(..., description="'portfolio' or 'benchmark'")
    period_start: date
    period_end: date
    return_pct: float = Field(..., description="Return as percentage, e.g., 5.23 for 5.23%")
    return_type: str = Field(default="TWR", description="TWR or MWR")
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class ESGRating(BaseModel):
    """ESG score and taxonomy alignment data.

    Combines quantitative ESG scores (0-10 scale) with qualitative risk
    levels and EU Taxonomy alignment percentages.
    """

    rating_id: str
    entity_id: str = Field(..., description="ISIN or portfolio_id being rated")
    overall_score: float = Field(..., ge=0, le=10)
    environmental_score: float | None = Field(None, ge=0, le=10)
    social_score: float | None = Field(None, ge=0, le=10)
    governance_score: float | None = Field(None, ge=0, le=10)
    risk_level: ESGRiskLevel
    taxonomy_alignment_pct: float | None = Field(None, ge=0, le=100)
    controversy_score: int | None = Field(None, ge=0, le=5, description="0=severe, 5=no issues")
    rating_date: date
    provider: str = Field(default="Sustainalytics")


class RatingProvider(BaseModel):
    """External data vendor providing ESG or fund ratings."""

    provider_id: str
    name: str = Field(..., min_length=1)
    rating_type: str = Field(..., description="ESG, Fund Performance, Credit, etc.")


class FundManager(BaseModel):
    """Individual portfolio manager responsible for investment decisions."""

    manager_id: str
    name: str = Field(..., min_length=1)
    title: str | None = None
    years_experience: int | None = Field(None, ge=0)


class Entity(BaseModel):
    """Legal entity in the corporate structure (asset management company).

    Sourced from GLEIF LEI database. The PARENT_OF relationship models
    the corporate hierarchy (e.g., BlackRock Inc -> iShares).
    """

    entity_id: str = Field(..., description="LEI or internal ID")
    name: str = Field(..., min_length=1)
    entity_type: str = Field(default="Asset Manager")
    country: str = Field(default="DE", min_length=2, max_length=2)
    parent_entity_id: str | None = None
