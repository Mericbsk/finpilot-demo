"""Unified FinPilot Score — Sprint 5 T4

Combines scanner composite score with DRL agent confidence into a single
0-100 score that rewards agreement and penalises conflict.

Formula
-------
    base  = 0.6 × (scanner_composite / 100) + 0.4 × drl_confidence
    score = base × (1 + α × agreement)

where:
    α = 0.3  (agreement weight)

    agreement:
      +1.0  → scanner & DRL both agree (same signal)
       0.0  → DRL is HOLD, or DRL cache is stale / unavailable
      -0.5  → scanner & DRL conflict (e.g. scanner BUY, DRL SELL)
"""

from __future__ import annotations

_ALPHA = 0.3  # agreement weight


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

    base = 0.6 * sc + 0.4 * dc

    # Anlaşma çarpanı
    if drl_signal == "HOLD":
        agreement = 0.0
    elif drl_signal == scanner_signal:
        agreement = 1.0
    else:
        agreement = -0.5  # çelişki cezası

    raw = base * (1.0 + _ALPHA * agreement)
    return min(100, max(0, int(round(raw * 100))))
