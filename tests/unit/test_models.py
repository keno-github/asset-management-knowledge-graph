"""Unit tests for Pydantic domain models.

Tests validation rules, default values, and edge cases for all node types.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from amkg.models.enums import AssetClass, AssetType, ESGRiskLevel, MorningstarRating
from amkg.models.nodes import (
    Asset,
    Benchmark,
    Entity,
    ESGRating,
    FundManager,
    Holding,
    PerformanceRecord,
    Portfolio,
    RatingProvider,
    Sector,
)
from amkg.models.relationships import (
    BelongsTo,
    ComposedOf,
    HasESGScore,
    Holds,
    ManagedBy,
    MeasuredAgainst,
    ParentOf,
    PeerOf,
    RatedBy,
    Tracks,
    WorksFor,
)

# ============================================================
# PORTFOLIO
# ============================================================


class TestPortfolio:
    def test_valid_portfolio(self, sample_portfolio: Portfolio) -> None:
        assert sample_portfolio.portfolio_id == "ETF001"
        assert sample_portfolio.asset_class == AssetClass.EQUITY
        assert sample_portfolio.morningstar_rating == MorningstarRating.FOUR_STAR

    def test_portfolio_minimal(self) -> None:
        p = Portfolio(portfolio_id="X", name="Test Fund", asset_class=AssetClass.EQUITY)
        assert p.currency == "EUR"
        assert p.is_active is True
        assert p.aum is None

    def test_portfolio_invalid_isin(self) -> None:
        with pytest.raises(ValidationError, match="isin"):
            Portfolio(
                portfolio_id="X",
                name="Bad ISIN Fund",
                isin="INVALID",
                asset_class=AssetClass.EQUITY,
            )

    def test_portfolio_valid_isin_format(self) -> None:
        p = Portfolio(
            portfolio_id="X",
            name="Good Fund",
            isin="IE00B4K48X80",
            asset_class=AssetClass.EQUITY,
        )
        assert p.isin == "IE00B4K48X80"

    def test_portfolio_negative_aum_rejected(self) -> None:
        with pytest.raises(ValidationError, match="aum"):
            Portfolio(
                portfolio_id="X", name="Bad AUM", asset_class=AssetClass.EQUITY, aum=-100
            )

    def test_portfolio_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Portfolio(portfolio_id="X", name="", asset_class=AssetClass.EQUITY)

    def test_portfolio_strips_whitespace(self) -> None:
        p = Portfolio(
            portfolio_id="X", name="  Trimmed Fund  ", asset_class=AssetClass.EQUITY
        )
        assert p.name == "Trimmed Fund"


# ============================================================
# ASSET
# ============================================================


class TestAsset:
    def test_valid_asset(self, sample_asset: Asset) -> None:
        assert sample_asset.isin == "NL0010273215"
        assert sample_asset.sector == "Information Technology"

    def test_asset_requires_isin(self) -> None:
        with pytest.raises(ValidationError):
            Asset(name="No ISIN Stock", asset_type=AssetType.COMMON_STOCK)  # type: ignore[call-arg]

    def test_asset_invalid_isin(self) -> None:
        with pytest.raises(ValidationError, match="isin"):
            Asset(isin="bad", name="Bad Stock")

    def test_asset_country_length(self) -> None:
        with pytest.raises(ValidationError, match="country"):
            Asset(isin="NL0010273215", name="Test", country="NLD")


# ============================================================
# BENCHMARK
# ============================================================


class TestBenchmark:
    def test_valid_benchmark(self, sample_benchmark: Benchmark) -> None:
        assert sample_benchmark.provider == "MSCI"
        assert sample_benchmark.asset_class == AssetClass.EQUITY

    def test_benchmark_defaults(self) -> None:
        b = Benchmark(
            benchmark_id="B1", name="Test Index", provider="STOXX", asset_class=AssetClass.EQUITY
        )
        assert b.currency == "EUR"
        assert b.region is None


# ============================================================
# HOLDING
# ============================================================


class TestHolding:
    def test_valid_holding(self, sample_holding: Holding) -> None:
        assert sample_holding.weight_pct == 4.52

    def test_holding_weight_range(self) -> None:
        with pytest.raises(ValidationError, match="weight_pct"):
            Holding(
                portfolio_id="X",
                isin="NL0010273215",
                weight_pct=150.0,
                as_of_date=date(2026, 1, 1),
            )

    def test_holding_negative_weight(self) -> None:
        with pytest.raises(ValidationError, match="weight_pct"):
            Holding(
                portfolio_id="X",
                isin="NL0010273215",
                weight_pct=-5.0,
                as_of_date=date(2026, 1, 1),
            )


# ============================================================
# ESG RATING
# ============================================================


class TestESGRating:
    def test_valid_esg(self, sample_esg_rating: ESGRating) -> None:
        assert sample_esg_rating.risk_level == ESGRiskLevel.LOW
        assert sample_esg_rating.controversy_score == 4

    def test_esg_score_range(self) -> None:
        with pytest.raises(ValidationError, match="overall_score"):
            ESGRating(
                rating_id="X",
                entity_id="Y",
                overall_score=15.0,
                risk_level=ESGRiskLevel.HIGH,
                rating_date=date(2026, 1, 1),
            )

    def test_esg_controversy_range(self) -> None:
        with pytest.raises(ValidationError, match="controversy_score"):
            ESGRating(
                rating_id="X",
                entity_id="Y",
                overall_score=5.0,
                risk_level=ESGRiskLevel.MEDIUM,
                controversy_score=10,
                rating_date=date(2026, 1, 1),
            )


# ============================================================
# SECTOR
# ============================================================


class TestSector:
    def test_valid_sector(self, sample_sector: Sector) -> None:
        assert sample_sector.classification_system == "GICS"
        assert sample_sector.level == 1

    def test_sector_level_range(self) -> None:
        with pytest.raises(ValidationError, match="level"):
            Sector(sector_id="X", name="Bad Level", level=5)


# ============================================================
# PERFORMANCE RECORD
# ============================================================


class TestPerformanceRecord:
    def test_valid_performance(self, sample_performance: PerformanceRecord) -> None:
        assert sample_performance.return_pct == 2.34
        assert sample_performance.return_type == "TWR"

    def test_performance_defaults(self) -> None:
        pr = PerformanceRecord(
            record_id="X",
            entity_id="Y",
            entity_type="portfolio",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            return_pct=-3.5,
        )
        assert pr.currency == "EUR"
        assert pr.return_type == "TWR"


# ============================================================
# ENTITY, FUND MANAGER, RATING PROVIDER
# ============================================================


class TestEntity:
    def test_valid_entity(self, sample_entity: Entity) -> None:
        assert sample_entity.country == "US"
        assert sample_entity.parent_entity_id == "LEI_BLACKROCK_INC"


class TestFundManager:
    def test_valid_manager(self, sample_fund_manager: FundManager) -> None:
        assert sample_fund_manager.years_experience == 18


class TestRatingProvider:
    def test_valid_provider(self, sample_rating_provider: RatingProvider) -> None:
        assert sample_rating_provider.rating_type == "ESG"


# ============================================================
# RELATIONSHIPS
# ============================================================


class TestRelationships:
    def test_tracks(self) -> None:
        t = Tracks(is_primary=True, effective_date=date(2026, 1, 1))
        assert t.is_primary is True

    def test_holds(self) -> None:
        h = Holds(weight_pct=5.0, as_of_date=date(2026, 1, 1))
        assert h.weight_pct == 5.0

    def test_holds_invalid_weight(self) -> None:
        with pytest.raises(ValidationError):
            Holds(weight_pct=200.0, as_of_date=date(2026, 1, 1))

    def test_belongs_to(self) -> None:
        b = BelongsTo()
        assert b.classification_system == "GICS"

    def test_composed_of(self) -> None:
        c = ComposedOf(weight_pct=2.5, as_of_date=date(2026, 1, 1))
        assert c.weight_pct == 2.5

    def test_peer_of(self) -> None:
        p = PeerOf(category="Europe Large-Cap", as_of_date=date(2026, 1, 1))
        assert p.category == "Europe Large-Cap"

    def test_parent_of(self) -> None:
        p = ParentOf(ownership_pct=100.0)
        assert p.ownership_pct == 100.0

    def test_managed_by_defaults(self) -> None:
        m = ManagedBy()
        assert m.role == "Lead Manager"

    def test_has_esg_score(self) -> None:
        h = HasESGScore(rating_date=date(2026, 1, 1))
        assert h.rating_date == date(2026, 1, 1)

    def test_measured_against(self) -> None:
        m = MeasuredAgainst(excess_return_pct=1.5)
        assert m.excess_return_pct == 1.5

    def test_rated_by(self) -> None:
        r = RatedBy(methodology="ESG Risk Ratings 2.0")
        assert r.methodology == "ESG Risk Ratings 2.0"

    def test_works_for(self) -> None:
        w = WorksFor(department="Equities")
        assert w.department == "Equities"
