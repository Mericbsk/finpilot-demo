"""FinPilot Score Calibration — Sprint 5 (S5-4).

Maps raw recommendation scores to empirical win probability using a simple
binned isotonic-style estimator. We deliberately avoid an sklearn dep — the
input volume is tiny (<= MAX_SIGNALS) and a band-based estimator is more
transparent for an autonomous system.

Pipeline:
    resolved_signals = [(score, win_bool), ...]   from kpi_tracker
    refit_calibration() bins by score, computes win-rate per band, then
    enforces monotonicity (cumulative max for ascending bands).
    calibrated_probability(score) -> float in [0, 1]

The fitted model is persisted to ``data/calibration.json`` and to Redis
key ``finpilot:calibration:v0`` for cross-process sharing.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Configurable Brier regression threshold (default 0.02 = 2pp degradation triggers rollback)
_BRIER_REGRESSION_THRESHOLD = float(
    os.getenv("FINPILOT_BRIER_REGRESSION_THRESHOLD", "0.02")
)

_REDIS_KEY = "finpilot:calibration:v0"
_DISK_PATH = Path("data") / "calibration.json"
_BRIER_HISTORY_PATH = Path("data") / "calibration_brier_history.json"
_MAX_BRIER_HISTORY = 90  # keep 90 daily entries

# Score bands — recommendation score range is ~0..18.3 (see scanner.score_engine)
# We use a slightly wider upper bound and uniform bins.
_DEFAULT_BANDS = [
    (0.0, 3.0),
    (3.0, 6.0),
    (6.0, 9.0),
    (9.0, 12.0),
    (12.0, 15.0),
    (15.0, 25.0),
]

_redis_client = None
_redis_unavailable = False
_mem_model: dict[str, Any] | None = None


def _get_redis():
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore

        from core.config import get_settings

        url = get_settings().redis_url
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception:
        _redis_unavailable = True
        return None


def _enforce_monotonic(probs: list[float]) -> list[float]:
    """Enforce non-decreasing sequence (isotonic-lite). higher score >= win rate."""
    out: list[float] = []
    running = 0.0
    for p in probs:
        running = max(running, p)
        out.append(round(running, 4))
    return out


def refit_calibration(
    samples: list[tuple[float, bool]] | None = None,
    min_samples_per_band: int = 5,
    bands: list[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Refit the score→probability mapping.

    Args:
        samples: list of (score, won_bool). If None, loads from kpi_tracker.
        min_samples_per_band: bands with fewer samples fall back to global rate.
        bands: optional band override (lower-inclusive, upper-exclusive).

    Returns the fitted model dict.
    """
    global _mem_model

    if samples is None:
        try:
            from core.kpi_tracker import _load_all_signals  # type: ignore

            sigs = _load_all_signals()
            samples = [
                (float(s.get("score", 0)), s.get("outcome") == "win")
                for s in sigs
                if s.get("outcome") is not None
            ]
        except Exception as exc:
            logger.debug("calibration.refit: kpi load failed: %s", exc)
            samples = []

    bands = bands or _DEFAULT_BANDS
    total = len(samples)
    global_rate = sum(1 for _, w in samples if w) / total if total > 0 else 0.5

    raw_band_rates: list[float] = []
    band_counts: list[int] = []
    for lo, hi in bands:
        in_band = [w for s, w in samples if lo <= s < hi]
        band_counts.append(len(in_band))
        if len(in_band) >= min_samples_per_band:
            raw_band_rates.append(sum(1 for w in in_band if w) / len(in_band))
        else:
            raw_band_rates.append(global_rate)

    monotonic_rates = _enforce_monotonic(raw_band_rates)

    model = {
        "version": "v0",
        "fitted_at": int(time.time()),
        "n_samples": total,
        "global_win_rate": round(global_rate, 4),
        "bands": [
            {"lo": lo, "hi": hi, "n": n, "raw_p": round(rp, 4), "p": p}
            for (lo, hi), n, rp, p in zip(
                bands, band_counts, raw_band_rates, monotonic_rates, strict=True
            )
        ],
    }

    _mem_model = model
    _persist_model(model)
    logger.info(
        "Calibration refit: n=%d global_p=%.3f bands=%d",
        total,
        global_rate,
        len(bands),
    )
    return model


def _persist_model(model: dict[str, Any]) -> None:
    try:
        _DISK_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DISK_PATH.write_text(json.dumps(model, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("calibration: disk persist failed: %s", exc)
    r = _get_redis()
    if r is not None:
        try:
            r.set(_REDIS_KEY, json.dumps(model))
        except Exception:
            pass


def _load_model() -> dict[str, Any] | None:
    global _mem_model
    if _mem_model is not None:
        return _mem_model
    r = _get_redis()
    if r is not None:
        try:
            raw = r.get(_REDIS_KEY)
            if raw:
                _mem_model = json.loads(raw)
                return _mem_model
        except Exception:
            pass
    try:
        if _DISK_PATH.exists():
            _mem_model = json.loads(_DISK_PATH.read_text(encoding="utf-8"))
            return _mem_model
    except Exception:
        pass
    return None


def calibrated_probability(score: float) -> float:
    """Return calibrated P(win) for a recommendation score in [0, 1].

    Returns 0.5 when no model has been fitted yet (graceful default).
    """
    model = _load_model()
    if model is None:
        return 0.5
    for band in model.get("bands", []):
        if band["lo"] <= score < band["hi"]:
            return float(band["p"])
    # Score above the highest band — clamp to last band's probability
    bands = model.get("bands") or []
    if bands:
        return float(bands[-1]["p"])
    return 0.5


def get_calibration_model() -> dict[str, Any] | None:
    """Return the current fitted calibration model (None if not fitted)."""
    return _load_model()


def _probability_for(model: dict[str, Any], score: float) -> float:
    for band in model.get("bands", []):
        if band["lo"] <= score < band["hi"]:
            return float(band["p"])
    bands = model.get("bands") or []
    return float(bands[-1]["p"]) if bands else 0.5


def _brier(model: dict[str, Any], samples: list[tuple[float, bool]]) -> float:
    if not samples:
        return 0.25
    s = 0.0
    for score, won in samples:
        p = _probability_for(model, float(score))
        s += (p - (1.0 if won else 0.0)) ** 2
    return s / len(samples)


def _ece(model: dict[str, Any]) -> float:
    """Expected Calibration Error: weighted mean absolute deviation per band."""
    bands = model.get("bands", [])
    total = model.get("n_samples", 0)
    if total == 0:
        return 0.0
    ece = 0.0
    for band in bands:
        n = band.get("n", 0)
        if n == 0:
            continue
        observed = band.get("raw_p", band["p"])
        predicted = band["p"]
        ece += (n / total) * abs(observed - predicted)
    return round(ece, 4)


def _append_brier_history(brier: float) -> None:
    """Append a timestamped Brier score to the rolling history file."""
    try:
        history: list[dict[str, Any]] = []
        if _BRIER_HISTORY_PATH.exists():
            history = json.loads(_BRIER_HISTORY_PATH.read_text(encoding="utf-8"))
        history.append({"ts": int(time.time()), "brier": round(brier, 4)})
        if len(history) > _MAX_BRIER_HISTORY:
            history = history[-_MAX_BRIER_HISTORY:]
        _BRIER_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _BRIER_HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("calibration: brier history persist failed: %s", exc)


def get_brier_history() -> list[dict[str, Any]]:
    """Return stored Brier history entries [{ts, brier}, ...]."""
    try:
        if _BRIER_HISTORY_PATH.exists():
            return json.loads(_BRIER_HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def get_calibration_stats() -> dict[str, Any]:
    """Return calibration quality metrics for the dashboard."""
    from core.kpi_tracker import compute_decile_lift

    model = _load_model()
    decile_data = compute_decile_lift()

    samples: list[tuple[float, bool]] = []
    try:
        from core.kpi_tracker import _load_all_signals  # type: ignore

        sigs = _load_all_signals()
        samples = [
            (float(s.get("score", 0)), s.get("outcome") == "win")
            for s in sigs
            if s.get("outcome") is not None
        ]
    except Exception:
        pass

    current_brier: float | None = None
    current_ece: float | None = None
    bands_detail: list[dict[str, Any]] = []

    if model is not None:
        current_brier = round(_brier(model, samples), 4) if samples else None
        current_ece = _ece(model)
        bands_detail = model.get("bands", [])

    history = get_brier_history()

    return {
        "fitted": model is not None,
        "n_samples": len(samples),
        "brier": current_brier,
        "ece": current_ece,
        "bands": bands_detail,
        "decile_lift": decile_data,
        "brier_history": history,
    }


def refit_with_gate(
    *,
    min_samples_to_promote: int = 20,
    brier_tolerance: float | None = None,
) -> dict[str, Any]:
    """Faz 3: refit calibration but rollback to prior model if quality drops.

    Decision policy:
      - First-ever fit (no prior): always promote.
      - Candidate has < ``min_samples_to_promote`` resolved samples: rollback
        to prior to avoid promoting a noisy estimate.
      - Candidate Brier on outcome-tagged samples is worse than prior by more
        than ``brier_tolerance``: rollback.
      - Otherwise: promote.

    Every decision is recorded via core.audit_log.
    """
    from core import audit_log

    # Resolve effective tolerance: caller override > env var
    effective_tolerance = brier_tolerance if brier_tolerance is not None else _BRIER_REGRESSION_THRESHOLD

    prior = _load_model()

    candidate = refit_calibration()

    samples: list[tuple[float, bool]] = []
    try:
        from core.kpi_tracker import _load_all_signals  # type: ignore

        sigs = _load_all_signals()
        samples = [
            (float(s.get("score", 0)), s.get("outcome") == "win")
            for s in sigs
            if s.get("outcome") is not None
        ]
    except Exception as exc:
        logger.debug("calibration_gate: kpi load failed: %s", exc)

    n = candidate.get("n_samples", 0)

    if prior is None:
        audit_log.record(
            actor="calibration_gate",
            action="calibration.refit",
            decision="promoted_first",
            payload={"n_samples": n},
        )
        return {"promoted": True, "reason": "no_prior", "model": candidate}

    if n < min_samples_to_promote:
        _persist_model(prior)
        global _mem_model
        _mem_model = prior
        audit_log.record(
            actor="calibration_gate",
            action="calibration.refit",
            decision="rolled_back",
            payload={
                "reason": "insufficient_samples",
                "n_samples": n,
                "min_required": min_samples_to_promote,
            },
        )
        return {
            "promoted": False,
            "reason": "insufficient_samples",
            "n_samples": n,
            "model": prior,
        }

    new_brier = _brier(candidate, samples)
    old_brier = _brier(prior, samples)
    if new_brier > old_brier + effective_tolerance:
        _persist_model(prior)
        _mem_model = prior
        audit_log.record(
            actor="calibration_gate",
            action="calibration.refit",
            decision="rolled_back",
            payload={
                "reason": "degraded_brier",
                "new_brier": round(new_brier, 4),
                "old_brier": round(old_brier, 4),
                "tolerance": effective_tolerance,
            },
        )
        # Auto-disable: quality gate triggered by Brier regression
        try:
            from core.quality_gate import set_degraded

            set_degraded(
                reason=f"calibration_brier_regression: {new_brier:.4f} > {old_brier:.4f} + {effective_tolerance}",
                eval_report={
                    "overall_pass": False,
                    "metrics": {"new_brier": new_brier, "old_brier": old_brier},
                },
            )
        except Exception as _qg_exc:
            logger.debug("calibration_gate: quality_gate notify failed: %s", _qg_exc)
        return {
            "promoted": False,
            "reason": "degraded_brier",
            "new_brier": new_brier,
            "old_brier": old_brier,
            "model": prior,
        }

    audit_log.record(
        actor="calibration_gate",
        action="calibration.refit",
        decision="promoted",
        payload={
            "n_samples": n,
            "new_brier": round(new_brier, 4),
            "old_brier": round(old_brier, 4),
        },
    )
    _append_brier_history(new_brier)
    return {
        "promoted": True,
        "reason": "ok",
        "n_samples": n,
        "new_brier": new_brier,
        "old_brier": old_brier,
        "model": candidate,
    }
