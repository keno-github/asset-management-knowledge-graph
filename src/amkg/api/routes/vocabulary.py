"""SKOS vocabulary endpoints — sector and asset class taxonomies."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "ontology"


class SKOSConcept(BaseModel):
    uri: str
    pref_label: str
    alt_labels: list[str] = []
    definition: str | None = None
    notation: str | None = None


class SKOSConceptScheme(BaseModel):
    uri: str
    pref_label: str
    description: str
    concepts: list[SKOSConcept]
    turtle_download_url: str


_SECTORS = SKOSConceptScheme(
    uri="https://w3id.org/amkg/vocabulary/sectors#GICSScheme",
    pref_label="GICS Sector Classification",
    description="GICS Level-1 sectors with alternative labels for variant spellings used in iShares and ESG data sources.",
    turtle_download_url="/api/vocabulary/sectors.ttl",
    concepts=[
        SKOSConcept(
            uri="amkgv:Energy",
            pref_label="Energy",
            alt_labels=["Oil & Gas"],
            definition="Companies engaged in exploration, production, refining, and marketing of oil, gas, and consumable fuels.",
            notation="10",
        ),
        SKOSConcept(
            uri="amkgv:Materials",
            pref_label="Materials",
            alt_labels=["Basic Materials"],
            definition="Companies involved in the discovery, development, and processing of raw materials.",
            notation="15",
        ),
        SKOSConcept(
            uri="amkgv:Industrials",
            pref_label="Industrials",
            alt_labels=[],
            definition="Companies providing capital goods, commercial services, and transportation infrastructure.",
            notation="20",
        ),
        SKOSConcept(
            uri="amkgv:ConsumerDiscretionary",
            pref_label="Consumer Discretionary",
            alt_labels=["Consumer Cyclical"],
            definition="Companies providing non-essential goods and services whose demand is sensitive to economic cycles.",
            notation="25",
        ),
        SKOSConcept(
            uri="amkgv:ConsumerStaples",
            pref_label="Consumer Staples",
            alt_labels=["Consumer Non-cyclical", "Consumer Defensive"],
            definition="Companies providing essential everyday products whose demand remains stable regardless of economic conditions.",
            notation="30",
        ),
        SKOSConcept(
            uri="amkgv:HealthCare",
            pref_label="Health Care",
            alt_labels=["Healthcare"],
            definition="Companies in pharmaceuticals, biotechnology, medical devices, and healthcare services.",
            notation="35",
        ),
        SKOSConcept(
            uri="amkgv:Financials",
            pref_label="Financials",
            alt_labels=[],
            definition="Companies providing banking, insurance, asset management, and other financial services.",
            notation="40",
        ),
        SKOSConcept(
            uri="amkgv:InformationTechnology",
            pref_label="Information Technology",
            alt_labels=["Technology", "Tech"],
            definition="Companies in software, hardware, semiconductors, IT services, and electronic equipment.",
            notation="45",
        ),
        SKOSConcept(
            uri="amkgv:CommunicationServices",
            pref_label="Communication Services",
            alt_labels=["Communication", "Communications", "Telecommunication Services"],
            definition="Companies enabling communication and entertainment through media, internet, and telecom services.",
            notation="50",
        ),
        SKOSConcept(
            uri="amkgv:Utilities",
            pref_label="Utilities",
            alt_labels=[],
            definition="Companies providing electric, gas, water, and other utility services, typically regulated.",
            notation="55",
        ),
        SKOSConcept(
            uri="amkgv:RealEstate",
            pref_label="Real Estate",
            alt_labels=[],
            definition="Companies engaged in real estate investment trusts (REITs) and real estate management and development.",
            notation="60",
        ),
    ],
)

_ASSET_CLASSES = SKOSConceptScheme(
    uri="https://w3id.org/amkg/vocabulary/asset-classes#AssetClassScheme",
    pref_label="Asset Class Taxonomy",
    description="Broad asset classification for portfolios and benchmarks.",
    turtle_download_url="/api/vocabulary/asset-classes.ttl",
    concepts=[
        SKOSConcept(
            uri="amkgv:Equity",
            pref_label="Equity",
            alt_labels=["Equities", "Stocks", "Shares"],
            definition="Ownership stakes in companies, including common and preferred stock.",
        ),
        SKOSConcept(
            uri="amkgv:FixedIncome",
            pref_label="Fixed Income",
            alt_labels=["Bonds", "Debt", "Fixed Interest"],
            definition="Debt instruments including government bonds, corporate bonds, and other fixed-interest securities.",
        ),
        SKOSConcept(
            uri="amkgv:MoneyMarket",
            pref_label="Money Market",
            alt_labels=["Cash Equivalents"],
            definition="Short-term, highly liquid debt instruments with maturities typically under one year.",
        ),
        SKOSConcept(
            uri="amkgv:Alternatives",
            pref_label="Alternatives",
            alt_labels=["Alternative Investments"],
            definition="Non-traditional investments including hedge funds, private equity, and structured products.",
        ),
        SKOSConcept(
            uri="amkgv:RealEstate",
            pref_label="Real Estate",
            alt_labels=["Property", "REITs"],
            definition="Real estate investment trusts and direct property investments.",
        ),
        SKOSConcept(
            uri="amkgv:Commodities",
            pref_label="Commodities",
            alt_labels=["Raw Materials"],
            definition="Physical goods and natural resources including precious metals, energy, and agricultural products.",
        ),
        SKOSConcept(
            uri="amkgv:MultiAsset",
            pref_label="Multi Asset",
            alt_labels=["Multi-Asset", "Balanced", "Mixed"],
            definition="Strategies combining multiple asset classes within a single portfolio allocation.",
        ),
    ],
)


@router.get("/sectors", response_model=SKOSConceptScheme)
def get_sectors_vocabulary() -> SKOSConceptScheme:
    """GICS sector taxonomy as SKOS concepts with preferred and alternative labels."""
    return _SECTORS


@router.get("/asset-classes", response_model=SKOSConceptScheme)
def get_asset_classes_vocabulary() -> SKOSConceptScheme:
    """Asset class taxonomy as SKOS concepts."""
    return _ASSET_CLASSES


@router.get("/sectors.ttl")
def get_sectors_ttl() -> FileResponse:
    """Download the GICS sector vocabulary in Turtle format."""
    path = ONTOLOGY_DIR / "sectors.ttl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sectors vocabulary file not found")
    return FileResponse(path=path, media_type="text/turtle", filename="sectors.ttl")


@router.get("/asset-classes.ttl")
def get_asset_classes_ttl() -> FileResponse:
    """Download the asset class vocabulary in Turtle format."""
    path = ONTOLOGY_DIR / "asset-classes.ttl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset classes vocabulary file not found")
    return FileResponse(path=path, media_type="text/turtle", filename="asset-classes.ttl")
