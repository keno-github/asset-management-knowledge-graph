"""Unit tests for data quality validators."""

from datetime import date

from amkg.models.nodes import Holding
from amkg.pipeline.validators.quality import (
    validate_holdings_weights,
    validate_isin_format,
)


class TestHoldingsWeightValidation:
    def _make_holdings(self, portfolio_id: str, weights: list[float]) -> list[Holding]:
        return [
            Holding(
                portfolio_id=portfolio_id,
                isin=f"XX000000000{i}",
                weight_pct=w,
                as_of_date=date(2026, 1, 1),
            )
            for i, w in enumerate(weights)
        ]

    def test_valid_weights_sum_to_100(self) -> None:
        holdings = self._make_holdings("P1", [30.0, 25.0, 20.0, 15.0, 10.0])
        report = validate_holdings_weights(holdings)
        assert report.passed == 1
        assert len(report.errors) == 0

    def test_weights_within_tolerance(self) -> None:
        # 95% total — within 10% tolerance
        holdings = self._make_holdings("P1", [50.0, 45.0])
        report = validate_holdings_weights(holdings)
        assert report.passed == 1
        assert len(report.errors) == 0

    def test_weights_under_tolerance_warns(self) -> None:
        # 80% total — under by 20%, triggers warning
        holdings = self._make_holdings("P1", [50.0, 30.0])
        report = validate_holdings_weights(holdings)
        assert len(report.warnings) == 1
        assert "under by" in report.warnings[0]

    def test_weights_over_100_errors(self) -> None:
        # 120% total — over by 20%, triggers error
        holdings = self._make_holdings("P1", [60.0, 60.0])
        report = validate_holdings_weights(holdings)
        assert len(report.errors) == 1
        assert "over by" in report.errors[0]

    def test_multiple_portfolios(self) -> None:
        holdings = (
            self._make_holdings("P1", [50.0, 50.0])
            + self._make_holdings("P2", [30.0, 70.0])
        )
        report = validate_holdings_weights(holdings)
        assert report.total_checks == 2
        assert report.passed == 2


class TestISINValidation:
    def test_valid_isins(self) -> None:
        isins = ["NL0010273215", "IE00B4K48X80", "DE0007236101"]
        report = validate_isin_format(isins)
        assert report.passed == 3
        assert len(report.errors) == 0

    def test_invalid_isin_too_short(self) -> None:
        report = validate_isin_format(["NL123"])
        assert len(report.errors) == 1

    def test_invalid_isin_bad_prefix(self) -> None:
        report = validate_isin_format(["12ABCDEFGH01"])
        assert len(report.errors) == 1

    def test_mixed_valid_invalid(self) -> None:
        isins = ["NL0010273215", "INVALID", "IE00B4K48X80"]
        report = validate_isin_format(isins)
        assert report.passed == 2
        assert len(report.errors) == 1
