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

    agreement:
      +1.0  → scanner & DRL both agree (same signal)
       0.0  → DRL is HOLD, or DRL cache is stale / unavailable
      -0.5  → scanner & DRL conflict (e.g. scanner BUY, DRL SELL)
"""

from __future__ import annotations

_ALPHA = 0.3  # agreement weight
_W_DRL = 0.0  # DRL weight — set to 0 until live DRL is connected; was 0.4
_W_SCANNER = 1.0 - _W_DRL  # scanner weight (currently 1.0)


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
    sc = float(scanner_composite) / 100.0
    dc = float(drl_confidence) if drl_confidence is not None else 0.5

    base = _W_SCANNER * sc + _W_DRL * dc

    # Agreement multiplier only applies when DRL is active
    if _W_DRL == 0.0 or drl_signal is None or drl_signal == "HOLD" or drl_confidence is None:
        agreement = 0.0
    elif drl_signal == scanner_signal:
        agreement = 1.0
    else:
        agreement = -0.5  # conflict penalty

    raw = base * (1.0 + _ALPHA * agreement)
    return min(100, max(0, int(round(raw * 100))))
