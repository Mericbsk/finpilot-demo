"""Production-instrumented baseline data capture (Level B, observability only).

This module is PURE OBSERVABILITY. It does not change, weight, gate, or recompute
any score. It persists the intermediate baseline inputs that evaluate_symbol()
already computes but that are otherwise lost, so the production baseline can be
reconstructed later (see reports/full_baseline_reconstruction_compression_forensics).

Non-regression contract:
  - Emission failures are swallowed (logged at debug) and never propagate.
  - It is a no-op unless FINPILOT_INSTRUMENT_BASELINE=1 (default OFF).
  - It reads values from the already-computed result dict; it never recomputes them.

Output: append-only JSONL under data/backtest_out/production_instrumentation/.
One file per run: baseline_inputs_<run_id>.jsonl
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

INSTRUMENTATION_VERSION = "1.0"
_OUT_DIR = Path("data/backtest_out/production_instrumentation")

# Fields captured from the evaluate_symbol result dict. These names already exist
# in the production return dict; we capture, we do not compute.
_CAPTURE_FIELDS = (
    "symbol",
    "timestamp",
    "regime",
    "direction",
    "score",
    "filter_score",
    "volume_spike",
    "price_momentum",
    "trend_strength",
    "alignment_ratio",
    "momentum_ratio",
    "vol_regime",
    "composite_score",
    "recommendation_score",
    "score_component_breakdown",
    "score_component_total",
    "score_input",
    "score_feature_flags",
    "telemetry_version",
)


def _enabled() -> bool:
    return os.environ.get("FINPILOT_INSTRUMENT_BASELINE", "0") == "1"


def _git_commit() -> str | None:
    try:
        import subprocess

        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def emit_baseline_inputs(results: list[dict[str, Any]], scan_basis: str = "EOD") -> str | None:
    """Persist baseline input rows from evaluate_symbol result dicts. Returns run_id.

    Pure observability: reads existing values, never recomputes. Failures are
    logged and swallowed so they can never affect scoring/ranking.
    """
    if not _enabled():
        return None
    try:
        run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
        _OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = _OUT_DIR / f"baseline_inputs_{run_id}.jsonl"
        commit = _git_commit()
        rows = 0
        with open(path, "a", encoding="utf-8") as fh:
            for r in results:
                if not isinstance(r, dict):
                    continue
                rec: dict[str, Any] = {
                    "run_id": run_id,
                    "scan_basis": scan_basis,
                    "instrumentation_version": INSTRUMENTATION_VERSION,
                    "git_commit": commit,
                    "scan_ts_utc": datetime.now(UTC).isoformat(),
                }
                for k in _CAPTURE_FIELDS:
                    rec[k] = r.get(k)
                # scan_date derived from the result's own signal timestamp when present
                rec["scan_date"] = str(r.get("timestamp", ""))[:10] or None
                fh.write(json.dumps(rec, default=str) + "\n")
                rows += 1
        logger.info("baseline instrumentation: wrote %d rows -> %s", rows, path)
        return run_id
    except Exception as e:  # noqa: BLE001
        logger.debug("baseline instrumentation failed (non-fatal): %s", e)
        return None
