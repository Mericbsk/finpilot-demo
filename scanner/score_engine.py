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


def compute_recommendation_score(row: dict[str, Any]) -> float:
    """Compute composite recommendation score from signal components.

    Args:
        row: Dictionary with signal data

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
    return round(score, 3)


def compute_recommendation_strength(x: Any) -> int:
    """Scale recommendation score to 0-100 range.

    Args:
        x: Either a row dict or raw score value

    Returns:
        Strength percentage (0-100)
    """
    try:
        if isinstance(x, dict) or hasattr(x, "get"):
            score = compute_recommendation_score(x)
        else:
            score = float(x)
        strength = max(0.0, min(100.0, (score / MAX_RECO_SCORE) * 100.0))
        return int(round(strength))
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.debug("Signal strength calculation failed: %s", e)
        return 0
