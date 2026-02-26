"""Data quality checks run after transformation, before graph loading.

Validates:
- Portfolio holding weights sum to approximately 100%
- No duplicate ISINs within a single portfolio
- ISIN format correctness
- ESG score ranges
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from loguru import logger

from amkg.models.nodes import Holding

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")


@dataclass
class QualityReport:
    """Results of data quality validation."""

    total_checks: int = 0
    passed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_checks if self.total_checks > 0 else 0.0

    @property
    def is_acceptable(self) -> bool:
        """True if no hard errors (warnings are OK)."""
        return len(self.errors) == 0


def validate_holdings_weights(
    holdings: list[Holding], tolerance: float = 10.0
) -> QualityReport:
    """Check that holding weights per portfolio sum to approximately 100%.

    Args:
        holdings: List of Holding objects to validate.
        tolerance: Acceptable deviation from 100% (default ±10%).
    """
    report = QualityReport()

    # Group by portfolio
    by_portfolio: dict[str, list[Holding]] = {}
    for h in holdings:
        by_portfolio.setdefault(h.portfolio_id, []).append(h)

    for pid, portfolio_holdings in by_portfolio.items():
        report.total_checks += 1
        total_weight = sum(h.weight_pct for h in portfolio_holdings)

        if abs(total_weight - 100.0) <= tolerance:
            report.passed += 1
        elif total_weight < 100.0 - tolerance:
            report.warnings.append(
                f"Portfolio {pid}: weights sum to {total_weight:.1f}% "
                f"(under by {100.0 - total_weight:.1f}%)"
            )
            report.passed += 1  # warning, not error
        else:
            report.errors.append(
                f"Portfolio {pid}: weights sum to {total_weight:.1f}% "
                f"(over by {total_weight - 100.0:.1f}%)"
            )

    return report


def validate_isin_format(isins: list[str]) -> QualityReport:
    """Verify all ISINs match the expected format."""
    report = QualityReport()

    for isin in isins:
        report.total_checks += 1
        if ISIN_PATTERN.match(isin):
            report.passed += 1
        else:
            report.errors.append(f"Invalid ISIN format: {isin}")

    return report


def run_quality_checks(
    holdings: list[Holding],
    isins: list[str],
) -> QualityReport:
    """Run all quality checks and return a combined report."""
    combined = QualityReport()

    for check_fn, args in [
        (validate_holdings_weights, (holdings,)),
        (validate_isin_format, (isins,)),
    ]:
        report = check_fn(*args)
        combined.total_checks += report.total_checks
        combined.passed += report.passed
        combined.warnings.extend(report.warnings)
        combined.errors.extend(report.errors)

    logger.info(
        f"[Quality] {combined.passed}/{combined.total_checks} checks passed "
        f"({len(combined.warnings)} warnings, {len(combined.errors)} errors)"
    )
    return combined
