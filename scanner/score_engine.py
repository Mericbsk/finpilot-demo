"""Scanner Score Engine — Sprint 5 T2

Composite recommendation scoring extracted from scanner/signals.py so
it can be unit-tested and modified independently of the signal pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Theoretical maximum composite score after premium-bonus removal
# (profitcore_audit 2026-05-23 showed inverted decile lift; removing subjective
# components is the first step in the simplification plan.)
MAX_RECO_SCORE: float = 18.0


def compute_recommendation_score(
    row: dict[str, Any], sentiment_score: float | None = None
) -> float:
    """Compute composite recommendation score from signal components.

    Args:
        row: Dictionary with signal data
        sentiment_score: Optional 0.0-1.0 FinBERT sentiment (0.5=neutral).
                         INT-4: When provided, adds a ±0.5 sentiment boost/penalty.

    Returns:
        Recommendation score (0 to ~18.0)
    """
    score = 0.0
    score += 2.0 if bool(row.get("regime", False)) else 0.0
    score += 2.0 if bool(row.get("direction", False)) else 0.0
    score += float(row.get("score", 0)) * 1.0
    score += float(row.get("filter_score", 0)) * 1.5
    score += float(row.get("alignment_ratio", 0.0)) * 2.0
    score += float(row.get("momentum_ratio", 0.0)) * 2.0
    score += 0.5 if bool(row.get("volume_spike", False)) else 0.0
    score += 0.5 if bool(row.get("price_momentum", False)) else 0.0
    score += 0.5 if bool(row.get("trend_strength", False)) else 0.0

    # INT-4: FinBERT sentiment boost (±0.5, neutral at 0.5)
    # Positive sentiment (>0.6): +0.5 boost
    # Negative sentiment (<0.4): -0.5 penalty
    if sentiment_score is not None:
        _SENTIMENT_WEIGHT = 0.5
        sentiment_delta = (float(sentiment_score) - 0.5) * 2.0 * _SENTIMENT_WEIGHT
        score += sentiment_delta

    return round(score, 3)


# ── Regime × Score-Band Gate ─────────────────────────────────────────────────
# Empirical thresholds from 2026-06-12 barrier audit (n=4 066 resolved signals)
# Bear Q2 (composite 30–55): wr=42.7%, avg=+1.48%, PF=2.18  → BOOST ×1.3
# Bear Q4 (composite > 62):  wr=28.9%, avg=+0.69%            → SUPPRESS ×0.5
# Bull D10 (composite > 62): wr=25.0%                        → SUPPRESS ×0.75
# All other segments:         neutral                         → ×1.0
_BEAR_BOOST_LOW: int = 30
_BEAR_BOOST_HIGH: int = 55
_HIGH_SCORE_THRESH: int = 62
_BEAR_BOOST_MULT: float = 1.3
_BEAR_SUPPRESS_MULT: float = 0.5
_BULL_SUPPRESS_MULT: float = 0.75


def regime_gate_mult(regime_bull: bool, composite_score: int) -> float:
    """Return position-size multiplier based on regime × composite-score band.

    Args:
        regime_bull:     True if market is in Bull regime (price > EMA200).
        composite_score: 0-100 composite strength from compute_recommendation_strength.

    Returns:
        Multiplier to apply to base position size (0.5, 0.75, 1.0, or 1.3).
    """
    if not regime_bull:  # Bear
        if _BEAR_BOOST_LOW <= composite_score <= _BEAR_BOOST_HIGH:
            return _BEAR_BOOST_MULT
        if composite_score > _HIGH_SCORE_THRESH:
            return _BEAR_SUPPRESS_MULT
    else:  # Bull
        if composite_score > _HIGH_SCORE_THRESH:
            return _BULL_SUPPRESS_MULT
    return 1.0


def compute_recommendation_strength(x: Any, sentiment_score: float | None = None) -> int:
    """Scale recommendation score to 0-100 range.

    Args:
        x: Either a row dict or raw score value
        sentiment_score: Optional 0.0-1.0 FinBERT sentiment to incorporate (INT-4)

    Returns:
        Strength percentage (0-100)
    """
    try:
        if isinstance(x, dict) or hasattr(x, "get"):
            score = compute_recommendation_score(x, sentiment_score=sentiment_score)
        else:
            score = float(x)
        strength = max(0.0, min(100.0, (score / MAX_RECO_SCORE) * 100.0))
        return int(round(strength))
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.debug("Signal strength calculation failed: %s", e)
        return 0
