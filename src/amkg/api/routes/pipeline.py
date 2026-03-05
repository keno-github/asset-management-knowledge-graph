"""Pipeline refresh endpoint with persistent run history."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from loguru import logger

from amkg.api.deps import Neo4jDep
from amkg.graph.client import Neo4jClient
from amkg.graph.queries import CREATE_PIPELINE_RUN, GET_PIPELINE_RUN, LIST_PIPELINE_RUNS
from amkg.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter()

_lock = threading.Lock()
_status: dict = {"running": False, "last_result": None, "last_error": None}


def _extract_run_metrics(result: dict) -> dict:
    """Extract per-step metrics from the orchestrator result dict."""
    fetch = result.get("fetch", {})
    transform = result.get("transform", {})
    validate = result.get("validate", {})
    load = result.get("load", {})

    return {
        "fetch_files": fetch.get("ishares_files", 0),
        "fetch_records": fetch.get("total_records", 0),
        "transform_etfs": transform.get("etfs_processed", 0),
        "transform_assets": transform.get("total_assets", 0),
        "transform_holdings": transform.get("total_holdings", 0),
        "validate_pass_rate": validate.get("pass_rate", "0%"),
        "validate_warnings": validate.get("warnings", 0),
        "validate_errors": validate.get("errors", 0),
        "load_portfolios": load.get("portfolios", 0),
        "load_assets": load.get("assets", 0),
        "load_sectors": load.get("sectors", 0),
        "load_holds": load.get("holds", 0),
        "load_esg_ratings": load.get("esg_ratings", 0),
    }


def _persist_run(
    run_id: str,
    started_at: str,
    completed_at: str,
    duration_seconds: float,
    status: str,
    metrics: dict,
    valuation_date: str | None,
    error_message: str | None,
) -> None:
    """Write a PipelineRun node to Neo4j."""
    try:
        client = Neo4jClient()
        try:
            params = {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": round(duration_seconds, 1),
                "status": status,
                "valuation_date": valuation_date,
                "error_message": error_message,
                **metrics,
            }
            client.run_write(CREATE_PIPELINE_RUN, params)
            logger.info(f"PipelineRun node created: {run_id} ({status})")
        finally:
            client.close()
    except Exception as e:
        logger.error(f"Failed to persist PipelineRun node: {e}")


def _run_pipeline() -> None:
    """Execute the pipeline in a background thread."""
    started_at = datetime.now(timezone.utc)
    start_time = time.monotonic()

    try:
        orchestrator = PipelineOrchestrator(
            steps=["all"], skip_yfinance=True, cache_ttl_override=0
        )
        result = orchestrator.run()

        completed_at = datetime.now(timezone.utc)
        duration = time.monotonic() - start_time
        metrics = _extract_run_metrics(result)

        # Extract actual valuation date from loaded portfolios
        valuation_date = result.get("load", {}).get("valuation_date")

        _persist_run(
            run_id=orchestrator.run_id,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_seconds=duration,
            status="success",
            metrics=metrics,
            valuation_date=valuation_date,
            error_message=None,
        )

        with _lock:
            _status["last_result"] = result
            _status["last_error"] = None

    except Exception as e:
        logger.error(f"Pipeline refresh failed: {e}")
        completed_at = datetime.now(timezone.utc)
        duration = time.monotonic() - start_time

        _persist_run(
            run_id=f"failed-{int(started_at.timestamp())}",
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_seconds=duration,
            status="failed",
            metrics=_extract_run_metrics({}),
            valuation_date=None,
            error_message=str(e),
        )

        with _lock:
            _status["last_error"] = str(e)
            _status["last_result"] = None
    finally:
        with _lock:
            _status["running"] = False


@router.post("/refresh")
def refresh_pipeline() -> dict:
    """Trigger a full pipeline refresh (fetch, transform, validate, load)."""
    with _lock:
        if _status["running"]:
            return {"status": "already_running"}
        _status["running"] = True
        _status["last_error"] = None
        _status["last_result"] = None

    thread = threading.Thread(target=_run_pipeline, daemon=True)
    thread.start()

    return {"status": "started"}


@router.get("/status")
def pipeline_status() -> dict:
    """Check pipeline run status."""
    with _lock:
        return {**_status}


@router.get("/history")
def pipeline_history(neo4j: Neo4jDep) -> list[dict]:
    """Return the last 50 pipeline runs from Neo4j."""
    rows = neo4j.run_query(LIST_PIPELINE_RUNS)
    return [row["run"] for row in rows]


@router.get("/history/{run_id}")
def pipeline_run_detail(run_id: str, neo4j: Neo4jDep) -> dict:
    """Return full details for a specific pipeline run."""
    rows = neo4j.run_query(GET_PIPELINE_RUN, {"run_id": run_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return rows[0]["run"]
