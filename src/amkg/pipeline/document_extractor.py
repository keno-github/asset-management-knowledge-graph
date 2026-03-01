"""Extract structured entities from unstructured documents using Claude.

Two-step process:
1. Extract raw text from PDF (via pdfplumber) or accept plain text
2. Send text to Claude with a structured extraction prompt
3. Return validated Pydantic models ready for Neo4j ingestion
"""

from __future__ import annotations

import json
from typing import Any

import pdfplumber
from anthropic import Anthropic
from loguru import logger
from pydantic import BaseModel

from amkg.config import settings

_MODEL = "claude-sonnet-4-20250514"
_MAX_TEXT_LENGTH = 30_000  # Truncate to avoid token limits

_EXTRACTION_PROMPT = """\
You are a financial document analyst. Extract structured entities from the document text below.

Return ONLY valid JSON matching this exact schema — no markdown fences, no explanation:

{{
  "portfolios": [
    {{
      "name": "string",
      "ticker": "string or null",
      "isin": "string (12 chars) or null",
      "asset_class": "Equity|Fixed Income|Multi-Asset|Commodity|null",
      "currency": "3-letter ISO code or null",
      "aum": "number in millions or null",
      "domicile": "2-letter ISO country or null"
    }}
  ],
  "holdings": [
    {{
      "portfolio_name": "string (must match a portfolio above)",
      "asset_name": "string",
      "ticker": "string or null",
      "isin": "string (12 chars) or null",
      "sector": "string or null",
      "weight_pct": "number 0-100 or null",
      "country": "2-letter ISO or null"
    }}
  ],
  "benchmarks": [
    {{
      "name": "string",
      "ticker": "string or null",
      "provider": "string or null",
      "asset_class": "string or null"
    }}
  ]
}}

Rules:
- ISINs must be exactly 12 characters. If unsure, set to null.
- AUM should be in millions (e.g., $1.2B = 1200).
- Weight percentages should be 0-100 (not 0-1).
- Set unknown fields to null — NEVER invent data.
- Extract ALL holdings you can find, even partial data.
- Match portfolio_name in holdings to the portfolio name exactly.

DOCUMENT TEXT:
{text}
"""


class ExtractedPortfolio(BaseModel):
    name: str
    ticker: str | None = None
    isin: str | None = None
    asset_class: str | None = None
    currency: str | None = None
    aum: float | None = None
    domicile: str | None = None


class ExtractedHolding(BaseModel):
    portfolio_name: str
    asset_name: str
    ticker: str | None = None
    isin: str | None = None
    sector: str | None = None
    weight_pct: float | None = None
    country: str | None = None


class ExtractedBenchmark(BaseModel):
    name: str
    ticker: str | None = None
    provider: str | None = None
    asset_class: str | None = None


class ExtractionResult(BaseModel):
    portfolios: list[ExtractedPortfolio] = []
    holdings: list[ExtractedHolding] = []
    benchmarks: list[ExtractedBenchmark] = []


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file.

    Args:
        file_bytes: Raw PDF bytes.

    Returns:
        Concatenated text from all pages.

    Raises:
        ValueError: If no text could be extracted.
    """
    import io

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("PDF contains no extractable text (may be scanned/image-only)")

    logger.info(f"Extracted {len(full_text)} chars from {len(text_parts)} PDF pages")
    return full_text


def extract_entities_from_text(text: str) -> ExtractionResult:
    """Send text to Claude for structured entity extraction.

    Args:
        text: Document text to analyze.

    Returns:
        ExtractionResult with portfolios, holdings, and benchmarks.

    Raises:
        RuntimeError: If Claude returns unparseable output.
    """
    # Truncate to stay within token limits
    if len(text) > _MAX_TEXT_LENGTH:
        logger.warning(f"Truncating text from {len(text)} to {_MAX_TEXT_LENGTH} chars")
        text = text[:_MAX_TEXT_LENGTH]

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": _EXTRACTION_PROMPT.format(text=text),
            }
        ],
    )

    raw_output = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        raw_output = "\n".join(lines[1:])
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        raw_output = raw_output.strip()

    try:
        data: dict[str, Any] = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {raw_output[:500]}")
        raise RuntimeError(f"Entity extraction failed: invalid JSON from LLM — {e}") from e

    result = ExtractionResult(
        portfolios=[ExtractedPortfolio(**p) for p in data.get("portfolios", [])],
        holdings=[ExtractedHolding(**h) for h in data.get("holdings", [])],
        benchmarks=[ExtractedBenchmark(**b) for b in data.get("benchmarks", [])],
    )

    logger.info(
        f"Extracted {len(result.portfolios)} portfolios, "
        f"{len(result.holdings)} holdings, "
        f"{len(result.benchmarks)} benchmarks"
    )
    return result
