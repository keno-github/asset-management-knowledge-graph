"""Pipeline refresh endpoint."""

from __future__ import annotations

import threading

from fastapi import APIRouter
from loguru import logger

from amkg.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter()

_lock = threading.Lock()
_status: dict = {"running": False, "last_result": None, "last_error": None}


def _run_pipeline() -> None:
    """Execute the pipeline in a background thread."""
    try:
        orchestrator = PipelineOrchestrator(
            steps=["all"], skip_yfinance=True, cache_ttl_override=0
        )
        result = orchestrator.run()
        with _lock:
            _status["last_result"] = result
            _status["last_error"] = None
    except Exception as e:
        logger.error(f"Pipeline refresh failed: {e}")
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
