"""Domain enumerations for asset management concepts."""

from enum import Enum


class AssetClass(str, Enum):
    """Broad asset classification used by portfolios and benchmarks."""

    EQUITY = "Equity"
    FIXED_INCOME = "Fixed Income"
    MONEY_MARKET = "Money Market"
    ALTERNATIVES = "Alternatives"
    REAL_ESTATE = "Real Estate"
    COMMODITIES = "Commodities"
    MULTI_ASSET = "Multi Asset"


class AssetType(str, Enum):
    """Security-level classification for individual assets."""

    COMMON_STOCK = "Common Stock"
    PREFERRED_STOCK = "Preferred Stock"
    CORPORATE_BOND = "Corporate Bond"
    GOVERNMENT_BOND = "Government Bond"
    ETF = "ETF"
    REIT = "REIT"
    CASH = "Cash"
    DERIVATIVE = "Derivative"
    OTHER = "Other"


class ESGRiskLevel(str, Enum):
    """Sustainalytics-style ESG risk categories."""

    NEGLIGIBLE = "Negligible"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    SEVERE = "Severe"


class MorningstarRating(int, Enum):
    """Morningstar star rating (1-5)."""

    ONE_STAR = 1
    TWO_STAR = 2
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5
