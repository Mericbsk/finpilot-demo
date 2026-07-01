"""Scanner Score Engine — Sprint 5 T2

Composite recommendation scoring extracted from scanner/signals.py so
it can be unit-tested and modified independently of the signal pipeline.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Theoretical maximum composite score after Faz 5 RSI/MACD demotion
# (score weight reduced ×1.0→×0.5, max score=3 → contributes 1.5 instead of 3.0)
# Previous MAX: 18.0 (with score×1.0). New ceiling: 16.5
# Components: regime 2 + direction 2 + score(max 3)×0.5=1.5 + filter(max 3)×1.5=4.5
#             + alignment_ratio(1.0)×2=2 + momentum_ratio(1.0)×2.5(low-vol)=2.5
#             + volume_spike 0.5 + price_momentum 0.5 + trend_strength 0.5 = 16.5
# The 0.5 reduction per good signal also means the upper suppression band
# needs a slight downward shift: _HIGH_SCORE_THRESH from 62→58 to preserve
# the same relative percentile cut-off in the composite 0-100 distribution.
MAX_RECO_SCORE: float = 16.5

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


# ── Lottery / MAX fade factor (Faz 1, env-gated, default OFF) ─────────────────
# Subtracts 0.0–_LOTTERY_WEIGHT from composite score.
# Bali-Cakici-Whitelaw lottery effect: high-MAX/high-IVOL/positive-skew stocks
# have systematically NEGATIVE expected returns. Factor computed in evaluate.py
# via scanner.features.compute_lottery_factor (pure pandas, no network call).
#
# Faz 2 (fade-vs-continuation): when BOTH lottery AND catalyst are enabled,
# a strong positive catalyst_factor (genuine PEAD/news event) partially offsets
# the lottery penalty — distinguishing a real event-continuation from a
# noise-driven lottery spike.
_LOTTERY_WEIGHT: float = 2.0


def _lottery_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_LOTTERY_FADE", "0") == "1"


# ── Overnight gap reversal factor (Faz 4, env-gated, default OFF) ─────────────
# Subtracts 0.0–_OVERNIGHT_WEIGHT from composite score.
# Large recent overnight gap-ups create short-term mean-reversion pressure.
# Factor computed in evaluate.py via scanner.features.compute_overnight_gap_factor.
_OVERNIGHT_WEIGHT: float = 1.0


def _overnight_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_OVERNIGHT_GAP", "0") == "1"


# ── Vol-regime scaled momentum weight (Faz 3) ─────────────────────────────────
# Low-vol momentum is cleaner alpha (fewer noise-driven spikes). High-vol
# momentum is less reliable — vol itself inflates pct-change z-scores.
# vol_regime: 0=low (σ<15%), 1=normal (15–30%), 2=high (>30%)
_VOL_REGIME_MOM_WEIGHTS: dict[int, float] = {0: 2.5, 1: 2.0, 2: 1.5}


# ── Alpha-v2 factors (env-gated, default OFF) ────────────────────────────────
# Evidence: 2026-06 real-data backtest (n=6410). gap% and RVOL are strong
# INDEPENDENT predictors absent from the legacy score; short interest is the
# single best signal (>=10% lift 2.57); 52w-high extension FADES (lift 0.68).
# The whole block is a no-op unless FINPILOT_ENABLE_ALPHA_V2=1, so default
# scoring/calibration is byte-for-byte unchanged.
_ALPHA_V2_GAP_WEIGHT: float = 2.0
_ALPHA_V2_RVOL_WEIGHT: float = 1.0
_ALPHA_V2_EXTENSION_WEIGHT: float = 1.5  # SUBTRACTED (over-extension fade)
_ALPHA_V2_SQUEEZE_WEIGHT: float = 3.0  # short-heavy squeeze, boosted vs 1.5
_ALPHA_V2_SCORE_MULT: float = 0.25  # RSI/MACD demoted further (was 0.5)


def _alpha_v2_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_ALPHA_V2", "0") == "1"


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
        row: Dictionary with signal data. Recognised keys:
             regime, direction, score, filter_score, alignment_ratio,
             momentum_ratio, volume_spike, price_momentum, trend_strength,
             vol_regime (Faz 3), squeeze_factor, catalyst_factor,
             lottery_factor (Faz 1/2), overnight_gap_factor (Faz 4).
        sentiment_score: Optional 0.0-1.0 FinBERT sentiment (0.5=neutral).
                         INT-4: When provided, adds a ±0.5 sentiment boost/penalty.

    Returns:
        Recommendation score (0 to ~18.0). Lottery/overnight penalties can
        push the value below 0; compute_recommendation_strength clamps at 0.
    """
    score = 0.0
    score += 2.0 if bool(row.get("regime", False)) else 0.0
    score += 2.0 if bool(row.get("direction", False)) else 0.0

    # Faz 5: RSI/MACD/volume raw-score demoted from ×1.0 → ×0.5.
    # These three binary checks (RSI in 30-70, volume > med×1.2, MACD hist rising)
    # are necessary but not sufficient — they act as a confirmation filter, not
    # the primary signal source. Reducing their weight prevents noise-driven
    # over-scoring while keeping the gate: entry_ok still requires score==3.
    _score_mult = _ALPHA_V2_SCORE_MULT if _alpha_v2_enabled() else 0.5
    score += float(row.get("score", 0)) * _score_mult

    # filter_score (volume_spike + price_momentum + trend_strength) remains at ×1.5:
    # these are the cleaner, longer-horizon confirmations from momentum analysis.
    score += float(row.get("filter_score", 0)) * 1.5
    score += float(row.get("alignment_ratio", 0.0)) * 2.0

    # Faz 3: vol-regime scaled momentum weight
    # Low-vol (0): weight 2.5 — clean momentum, trust more
    # Normal (1):  weight 2.0 — current baseline
    # High-vol (2): weight 1.5 — vol-inflated momentum, trust less
    # Note: use explicit None-check to avoid `0 or 1` falsy-trap.
    _vr = row.get("vol_regime")
    vol_regime = int(_vr) if _vr is not None else 1
    mom_weight = _VOL_REGIME_MOM_WEIGHTS.get(vol_regime, 2.0)
    score += float(row.get("momentum_ratio", 0.0)) * mom_weight

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
    if _squeeze_enabled() or _catalyst_enabled() or _alpha_v2_enabled():
        macro_mult = _macro_mult()
        if _squeeze_enabled() or _alpha_v2_enabled():
            squeeze = float(row.get("squeeze_factor", 0.0) or 0.0)
            _sq_w = _ALPHA_V2_SQUEEZE_WEIGHT if _alpha_v2_enabled() else _SQUEEZE_WEIGHT
            score += max(0.0, min(1.0, squeeze)) * _sq_w * macro_mult
        if _catalyst_enabled():
            catalyst = float(row.get("catalyst_factor", 0.0) or 0.0)
            score += max(-1.0, min(1.0, catalyst)) * _CATALYST_WEIGHT * macro_mult

    # ── Faz 1: Lottery / MAX fade penalty (env-gated, default OFF) ───────────
    # Subtracts up to _LOTTERY_WEIGHT (2.0) for high-MAX/high-IVOL/skew stocks.
    # Faz 2: Fade-vs-Continuation — a strong positive catalyst_factor (genuine
    # news/PEAD event) partially offsets the lottery penalty: real event-driven
    # continuation should not be penalised as a pure lottery fade.
    if _lottery_enabled():
        lottery = float(row.get("lottery_factor", 0.0) or 0.0)
        lottery_penalty = max(0.0, min(1.0, lottery)) * _LOTTERY_WEIGHT
        # Faz 2: catalyst relief — if catalyst > 0.3, reduce penalty by up to 50%
        # (catalyst 0.3→0.7 maps linearly to 0%→50% penalty reduction)
        if _catalyst_enabled():
            catalyst = float(row.get("catalyst_factor", 0.0) or 0.0)
            if catalyst > 0.3:
                catalyst_relief = min(0.5, (catalyst - 0.3) / 0.8)
                lottery_penalty *= 1.0 - catalyst_relief
        score -= lottery_penalty

    # ── Faz 4: Overnight gap reversal penalty (env-gated, default OFF) ────────
    # Subtracts up to _OVERNIGHT_WEIGHT (1.0) for recent large gap-up setups.
    if _overnight_enabled():
        overnight = float(row.get("overnight_gap_factor", 0.0) or 0.0)
        score -= max(0.0, min(1.0, overnight)) * _OVERNIGHT_WEIGHT

    # ── Alpha-v2 price-derived factors (FINPILOT_ENABLE_ALPHA_V2) ─────────────
    # gap% ve RVOL guclu bagimsiz tahminci; 52w-high asiri-uzama negatif.
    if _alpha_v2_enabled():
        gap_f = max(0.0, min(1.0, float(row.get("gap_factor", 0.0) or 0.0)))
        rvol_f = max(0.0, min(1.0, float(row.get("rvol_factor", 0.0) or 0.0)))
        ext_f = max(0.0, min(1.0, float(row.get("extension_factor", 0.0) or 0.0)))
        score += gap_f * _ALPHA_V2_GAP_WEIGHT
        score += rvol_f * _ALPHA_V2_RVOL_WEIGHT
        score -= ext_f * _ALPHA_V2_EXTENSION_WEIGHT

    return round(score, 3)


def effective_max_reco_score() -> float:
    """Return the composite-score normalisation ceiling.

    Kept fixed at ``MAX_RECO_SCORE`` even when the squeeze factor is enabled:
    widening the ceiling would re-scale every signal (including those with no
    squeeze data) and shift the calibration. Instead the squeeze factor acts as
    a pure additive boost on the numerator — symbols without squeeze data are an
    exact no-op, and squeeze symbols gain strength (clamped at 100).
    """
    if _alpha_v2_enabled():
        # Alpha-v2 adds up to gap(2)+rvol(1)+squeeze(3)=6 headroom; widen the
        # ceiling so boosted names are not saturated at 100. Non-boosted symbols
        # score on the same 0-16.5 base.
        return MAX_RECO_SCORE + 6.0
    return MAX_RECO_SCORE


# ── Regime × Score-Band Gate ─────────────────────────────────────────────────
# Empirical thresholds from 2026-06-12 barrier audit (n=4 066 resolved signals)
# Bear Q2 (composite 30–55): wr=42.7%, avg=+1.48%, PF=2.18  → BOOST ×1.3
# Bear Q4 (composite > 62):  wr=28.9%, avg=+0.69%            → SUPPRESS ×0.5
# Bull D10 (composite > 62): wr=25.0%                        → SUPPRESS ×0.75
# All other segments:         neutral                         → ×1.0
_BEAR_BOOST_LOW: int = 30
_BEAR_BOOST_HIGH: int = 55
# Faz 5b: lowered from 62→58 to match new score ceiling (16.5 vs 18.0).
# Maintains the same ~top-25% cut-off in the 0-100 composite distribution.
_HIGH_SCORE_THRESH: int = 58
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
