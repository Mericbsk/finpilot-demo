"""Unified FinPilot Score — Sprint 8 (DRL weight zeroed until live DRL connected)

Formula
-------
    base  = _W_SCANNER × (scanner_composite / 100)
            + _W_DRL × drl_confidence (inactive while _W_DRL == 0.0)
    score = base × (1 + α × agreement)

where:
    α = 0.3  (agreement weight)
    _W_DRL = 0.0  → DRL weight disabled until a real-time DRL is wired in
    _W_SCANNER = 1.0 - _W_DRL
"""

from __future__ import annotations

import threading

_ALPHA = 0.3  # agreement weight
_W_DRL = 0.0  # DRL weight — set to 0 until live DRL is connected; was 0.4
_W_SCANNER = 1.0 - _W_DRL  # scanner weight (currently 1.0)

# Named weights for the multi-factor ranker (loaded from registry champion on startup)
_weights: dict[str, float] = {}
_weights_lock = threading.Lock()


def get_weights() -> dict[str, float]:
    """Return a copy of the current named weight dict."""
    with _weights_lock:
        return dict(_weights)


def set_weights(new_weights: dict[str, float]) -> None:
    """Hot-reload named weights (called by calibration rollback / registry promote)."""
    with _weights_lock:
        _weights.clear()
        _weights.update(new_weights)


def load_weights() -> dict[str, float]:
    """Load champion weights from the model registry and apply them in-process."""
    try:
        from research.registry import ModelRegistry

        reg = ModelRegistry()
        champion = reg.get_champion()
        if champion and champion.get("weights"):
            set_weights(champion["weights"])
            return dict(champion["weights"])
    except Exception:
        pass
    return {}


def compute_finpilot_score(
    scanner_composite: int | float,
    scanner_signal: str,
    drl_signal: str | None,
    drl_confidence: float | None,
) -> int:
    """Compute the unified FinPilot Score (0-100).

    Args:
        scanner_composite: Scanner's 0-100 composite score
        scanner_signal:    "BUY" | "SELL" from scanner direction
        drl_signal:        "BUY" | "SELL" | "HOLD" | None from DRL cache
        drl_confidence:    0.0-1.0 confidence from DRL; None if unavailable

    Returns:
        Unified FinPilot Score 0-100
    """
    # DRL mevcut değilse composite_score'u olduğu gibi döndür.
    # Sahte/stale DRL confidence (varsayılan 0.5) skoru bozmasın.
    if drl_signal is None or drl_confidence is None:
        return min(100, max(0, int(round(float(scanner_composite)))))

    sc = float(scanner_composite) / 100.0
    dc = float(drl_confidence)

    base = _W_SCANNER * sc + _W_DRL * dc

    # Agreement multiplier only applies when DRL is active
    if _W_DRL == 0.0 or drl_signal is None or drl_signal == "HOLD" or drl_confidence is None:
        agreement = 0.0
    elif drl_signal == scanner_signal:
        agreement = 1.0
    else:
        agreement = -0.5  # çelişki cezası

    raw = base * (1.0 + _ALPHA * agreement)
    return min(100, max(0, int(round(raw * 100))))


# ---------------------------------------------------------------------------
# Re-export the composite recommendation scoring API so callers can rely on
# scanner.finpilot_score as the single public scoring surface.
# ---------------------------------------------------------------------------
from scanner.score_engine import (  # noqa: E402, F401
    MAX_RECO_SCORE,
    compute_recommendation_score,
    compute_recommendation_strength,
)

__all__ = [
    "compute_finpilot_score",
    "compute_recommendation_score",
    "compute_recommendation_strength",
    "MAX_RECO_SCORE",
    "get_weights",
    "set_weights",
    "load_weights",
]
