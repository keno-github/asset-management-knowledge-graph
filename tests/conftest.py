"""Shared test fixtures for the AMKG test suite."""

from datetime import date

import pytest

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


@pytest.fixture
def sample_portfolio() -> Portfolio:
    return Portfolio(
        portfolio_id="ETF001",
        name="iShares Core MSCI Europe UCITS ETF",
        isin="IE00B4K48X80",
        asset_class=AssetClass.EQUITY,
        currency="EUR",
        inception_date=date(2009, 9, 25),
        aum=8500.0,
        morningstar_category="Europe Large-Cap Blend Equity",
        morningstar_rating=MorningstarRating.FOUR_STAR,
        domicile="IE",
    )


@pytest.fixture
def sample_benchmark() -> Benchmark:
    return Benchmark(
        benchmark_id="MSCI_EU",
        name="MSCI Europe",
        ticker="MIEU",
        provider="MSCI",
        asset_class=AssetClass.EQUITY,
        currency="EUR",
        region="Europe",
    )


@pytest.fixture
def sample_asset() -> Asset:
    return Asset(
        isin="NL0010273215",
        name="ASML Holding NV",
        ticker="ASML",
        asset_type=AssetType.COMMON_STOCK,
        currency="EUR",
        country="NL",
        exchange="XAMS",
        market_cap=356000.0,
        sector="Information Technology",
        industry="Semiconductor Equipment",
    )


@pytest.fixture
def sample_sector() -> Sector:
    return Sector(
        sector_id="GICS_45",
        name="Information Technology",
        classification_system="GICS",
        level=1,
    )


@pytest.fixture
def sample_holding() -> Holding:
    return Holding(
        portfolio_id="ETF001",
        isin="NL0010273215",
        weight_pct=4.52,
        market_value=384200000.0,
        as_of_date=date(2026, 2, 25),
    )


@pytest.fixture
def sample_esg_rating() -> ESGRating:
    return ESGRating(
        rating_id="ESG_ASML",
        entity_id="NL0010273215",
        overall_score=7.2,
        environmental_score=6.8,
        social_score=7.0,
        governance_score=7.8,
        risk_level=ESGRiskLevel.LOW,
        taxonomy_alignment_pct=42.5,
        controversy_score=4,
        rating_date=date(2026, 1, 15),
        provider="Sustainalytics",
    )


@pytest.fixture
def sample_performance() -> PerformanceRecord:
    return PerformanceRecord(
        record_id="PERF_ETF001_2026_01",
        entity_id="ETF001",
        entity_type="portfolio",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        return_pct=2.34,
        return_type="TWR",
        currency="EUR",
    )


@pytest.fixture
def sample_entity() -> Entity:
    return Entity(
        entity_id="LEI_BLACKROCK",
        name="BlackRock Fund Advisors",
        entity_type="Asset Manager",
        country="US",
        parent_entity_id="LEI_BLACKROCK_INC",
    )


@pytest.fixture
def sample_fund_manager() -> FundManager:
    return FundManager(
        manager_id="MGR001",
        name="Michael Schmidt",
        title="Senior Portfolio Manager",
        years_experience=18,
    )


@pytest.fixture
def sample_rating_provider() -> RatingProvider:
    return RatingProvider(
        provider_id="SUST",
        name="Sustainalytics",
        rating_type="ESG",
    )
