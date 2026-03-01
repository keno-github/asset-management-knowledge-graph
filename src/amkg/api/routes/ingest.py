"""Document ingestion endpoint: PDF upload or text paste → Claude extraction → Neo4j.

Accepts either:
- A PDF file via multipart upload (field name: "file")
- Plain text via form field (field name: "text")

Three-phase pipeline:
1. Parse: Extract text from PDF or validate raw text
2. Extract: Claude identifies portfolios, holdings, benchmarks
3. Write: MERGE entities and relationships into Neo4j
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from amkg.api.deps import Neo4jDep
from amkg.config import settings
from amkg.pipeline.document_extractor import (
    extract_entities_from_text,
    extract_text_from_pdf,
)
from amkg.pipeline.document_loader import load_extraction_to_neo4j

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_MIN_TEXT_LENGTH = 50


@router.post("/extract")
async def extract_and_ingest(
    neo4j: Neo4jDep,
    file: UploadFile | None = File(None),  # noqa: B008
    text: str | None = Form(None),  # noqa: B008
) -> dict:
    """Extract entities from a document and ingest into the knowledge graph.

    Upload a PDF file OR paste plain text. The endpoint will:
    1. Extract text from the PDF (or use the provided text)
    2. Use Claude to identify financial entities (portfolios, holdings, benchmarks)
    3. Write the extracted entities to Neo4j

    Returns extraction results and graph write statistics.
    """
    # Guard: API key required
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "ANTHROPIC_API_KEY is not configured. "
                "Set it in your .env file to enable document extraction."
            ),
        )

    # Determine source type and extract text
    source_type: str
    doc_text: str

    if file and file.filename:
        # PDF upload path
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported. Got: {file.filename}",
            )

        content = await file.read()
        if len(content) > _MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {_MAX_FILE_SIZE // (1024 * 1024)}MB.",
            )

        try:
            doc_text = extract_text_from_pdf(content)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        source_type = "pdf"

    elif text:
        # Plain text path
        doc_text = text.strip()
        if len(doc_text) < _MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too short. Minimum {_MIN_TEXT_LENGTH} characters required.",
            )
        source_type = "text"

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either a PDF file upload or text content.",
        )

    # Phase 2: Claude extraction
    try:
        extraction = extract_entities_from_text(doc_text)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Phase 3: Neo4j write
    try:
        stats = load_extraction_to_neo4j(neo4j, extraction)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Graph write failed: {e}",
        ) from e

    return {
        "status": "success",
        "source_type": source_type,
        "text_length": len(doc_text),
        "extraction_model": "claude-sonnet-4-20250514",
        "entities": {
            "portfolios": [p.model_dump(mode="json") for p in extraction.portfolios],
            "holdings": [h.model_dump(mode="json") for h in extraction.holdings],
            "benchmarks": [b.model_dump(mode="json") for b in extraction.benchmarks],
        },
        "entity_counts": {
            "portfolios": len(extraction.portfolios),
            "holdings": len(extraction.holdings),
            "benchmarks": len(extraction.benchmarks),
        },
        "graph_writes": stats.to_dict(),
    }
