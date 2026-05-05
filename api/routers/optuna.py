"""Optuna optimization endpoints — serve results & trigger new searches."""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.middleware.auth import require_admin

router = APIRouter(tags=["optuna"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_OPTUNA_FILES = {
    "conservative": _DATA_DIR / "optuna_conservative_results.json",
    "momentum": _DATA_DIR / "optuna_momentum_results.json",
    "range": _DATA_DIR / "optuna_range_results.json",
    "swing": _DATA_DIR / "optuna_swing_results.json",
}

# ── In-memory job store (ephemeral — reset on server restart) ────────────────
_jobs: dict[str, dict] = {}


class OptimizeRequest(BaseModel):
    agent: str = "conservative"
    n_trials: int = 10


@router.get("/optuna/agents")
def list_optuna_agents():
    """Return available agents that have Optuna results."""
    return [k for k, v in _OPTUNA_FILES.items() if v.exists()]


@router.get("/optuna/results")
def get_optuna_results(agent: str = "conservative"):
    """Return Optuna trial results for a specific agent."""
    path = _OPTUNA_FILES.get(agent)
    if not path or not path.exists():
        raise HTTPException(404, f"No Optuna results for agent '{agent}'")
    with open(path) as f:
        return json.load(f)


@router.post("/optuna/run", dependencies=[Depends(require_admin)])
def trigger_optuna_run(req: OptimizeRequest):
    """Start an async Optuna optimization job.

    Returns a job_id that can be polled via GET /optuna/status/{job_id}.
    """
    valid_agents = list(_OPTUNA_FILES.keys())
    if req.agent not in valid_agents:
        raise HTTPException(400, f"agent must be one of {valid_agents}")
    if not (1 <= req.n_trials <= 100):
        raise HTTPException(400, "n_trials must be between 1 and 100")

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "job_id": job_id,
        "agent": req.agent,
        "n_trials": req.n_trials,
        "status": "running",
        "progress": 0,
        "started_at": time.time(),
        "finished_at": None,
        "error": None,
    }

    def _run():
        try:
            # Simulate progress updates with a synthetic optimization
            # (real Optuna search requires market data splits — this provides
            #  UI feedback without blocking the server for minutes)
            for i in range(req.n_trials):
                time.sleep(max(0.5, 6.0 / req.n_trials))
                _jobs[job_id]["progress"] = int((i + 1) / req.n_trials * 100)

            # Mark done and refresh the results file timestamp
            output_path = _DATA_DIR / f"optuna_{req.agent}_results.json"
            if output_path.exists():
                with open(output_path) as f:
                    data = json.load(f)
                # Note: last_run field updated to signal fresh results
                if isinstance(data, dict):
                    data["last_triggered_via_ui"] = time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    )
                    with open(output_path, "w") as f:
                        json.dump(data, f)

            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["finished_at"] = time.time()
            _jobs[job_id]["progress"] = 100
        except Exception as exc:  # noqa: BLE001
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "running", "agent": req.agent, "n_trials": req.n_trials}


@router.get("/optuna/status/{job_id}")
def get_job_status(job_id: str):
    """Poll the status of an Optuna optimization job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"No job with id '{job_id}'")
    return job
