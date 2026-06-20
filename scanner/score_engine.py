"""Scanner Score Engine — Sprint 5 T2

Composite recommendation scoring extracted from scanner/signals.py so
it can be unit-tested and modified independently of the signal pipeline.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Theoretical maximum composite score after premium-bonus removal
# (profitcore_audit 2026-05-23 showed inverted decile lift; removing subjective
# components is the first step in the simplification plan.)
MAX_RECO_SCORE: float = 18.0

# ── Float/Short squeeze factor (env-gated, default OFF) ──────────────────────
# Additive 0.0–1.0 squeeze potential (scanner.features.compute_squeeze_factor)
# scaled by this weight. Disabled by default so live scoring is unchanged until
# component_ablation validates marginal lift in the >30% move bucket.
_SQUEEZE_WEIGHT: float = 1.5


def _squeeze_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_SQUEEZE_FACTOR", "0") == "1"


# ── SEC EDGAR catalyst factor (env-gated, default OFF) ───────────────────────
# Signed -1.0..1.0 catalyst score (scanner.catalyst.compute_catalyst_factor):
# 8-K/Form4 push positive, S-1/424B offerings push negative. Scaled by this
# weight. Disabled by default; validate with component_ablation before enabling.
_CATALYST_WEIGHT: float = 1.5


def _catalyst_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_EDGAR_CATALYST", "0") == "1"


def _macro_mult() -> float:
    """Return the FRED macro multiplier for the new factors (1.0 when disabled).

    Dampens squeeze/catalyst additive terms in a risk-off regime so small-cap
    plays are sized down when the macro backdrop is hostile.
    """
    if os.environ.get("FINPILOT_ENABLE_FRED_MACRO", "0") != "1":
        return 1.0
    try:
        from core.macro_regime import macro_factor_multiplier  # noqa: PLC0415

        return macro_factor_multiplier()
    except Exception:  # noqa: BLE001
        return 1.0


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

    # Float/Short squeeze factor (env-gated, default OFF). Additive 0.0–1.5.
    # SEC EDGAR catalyst factor (env-gated, default OFF). Signed ±1.5.
    # Both are dampened by the FRED macro multiplier in a risk-off regime.
    if _squeeze_enabled() or _catalyst_enabled():
        macro_mult = _macro_mult()
        if _squeeze_enabled():
            squeeze = float(row.get("squeeze_factor", 0.0) or 0.0)
            score += max(0.0, min(1.0, squeeze)) * _SQUEEZE_WEIGHT * macro_mult
        if _catalyst_enabled():
            catalyst = float(row.get("catalyst_factor", 0.0) or 0.0)
            score += max(-1.0, min(1.0, catalyst)) * _CATALYST_WEIGHT * macro_mult

    return round(score, 3)


def effective_max_reco_score() -> float:
    """Return the composite-score normalisation ceiling.

    Kept fixed at ``MAX_RECO_SCORE`` even when the squeeze factor is enabled:
    widening the ceiling would re-scale every signal (including those with no
    squeeze data) and shift the calibration. Instead the squeeze factor acts as
    a pure additive boost on the numerator — symbols without squeeze data are an
    exact no-op, and squeeze symbols gain strength (clamped at 100).
    """
    return MAX_RECO_SCORE


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
        strength = max(0.0, min(100.0, (score / effective_max_reco_score()) * 100.0))
        return int(round(strength))
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.debug("Signal strength calculation failed: %s", e)
        return 0
