"""Signal Generation and Filtering Module

Contains all signal detection, filtering, and scoring functions.
Extracted from scanner.py for modularity and reusability.
"""

import logging
import math
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config import SETTINGS

# Configure module logger
logger = logging.getLogger(__name__)


# ---- Helper Functions ----
def safe_float(value: Any) -> float:
    """
    Safely convert pandas Series or single value to float.

    Args:
        value: Can be pandas Series, numpy array, or scalar

    Returns:
        Float value (0.0 if conversion fails or empty)
    """
    if hasattr(value, "iloc"):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    elif hasattr(value, "values"):
        return float(value.values[0]) if len(value.values) > 0 else 0.0
    else:
        return float(value)


# ---- Volume Analysis ----
def check_volume_spike(df: pd.DataFrame) -> bool:
    """
    Check if current volume exceeds average volume by configured multiplier.

    Args:
        df: DataFrame with 'Volume' and 'vol_avg10' columns

    Returns:
        True if volume spike detected
    """
    if len(df) < 10:
        return False
    try:
        current_vol = safe_float(df["Volume"].iloc[-1])
        avg_vol = safe_float(df["vol_avg10"].iloc[-1])
        return current_vol > avg_vol * SETTINGS.get("vol_multiplier", 1.5)
    except (KeyError, ValueError, IndexError) as e:
        logger.debug("Volume spike check failed: %s", e)
        return False


# ---- Momentum Analysis ----
def analyze_price_momentum(
    df: Optional[pd.DataFrame],
    *,
    windows: Optional[List[int]] = None,
    baseline_window: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Adaptive momentum profile generator with multi-horizon analysis.

    Produces per-horizon return percentages, z-scores, and reference statistics.
    Supports dynamic threshold calibration based on liquidity segments.

    Args:
        df: DataFrame with 'Close' and 'vol_avg10' columns
        windows: List of lookback periods to analyze (default from SETTINGS)
        baseline_window: Baseline window for z-score calculation (default from SETTINGS)

    Returns:
        Dictionary with:
        - metrics: List of per-horizon analysis dicts
        - best: The metric with highest absolute z-score
        - positive/negative: Boolean flags for significant moves
        - dominant_zscore, dominant_return_pct, dominant_direction
        - z_threshold_* values (effective, base, segment, dynamic)
        - liquidity_segment, baseline_window, dynamic_threshold_samples
    """
    close = df.get("Close") if df is not None else None
    if close is None or close.dropna().empty:
        return {
            "metrics": [],
            "best": None,
            "positive": False,
            "negative": False,
            "dominant_zscore": 0.0,
            "dominant_return_pct": 0.0,
            "dominant_direction": 0,
        }

    horizons = windows or SETTINGS.get("momentum_windows", [1, 3, 5])
    baseline_window = int(baseline_window or SETTINGS.get("momentum_baseline_window", 20))
    base_threshold = float(SETTINGS.get("momentum_z_threshold", 1.5))

    # Segment-based threshold by liquidity
    segment = None
    segment_threshold = None
    segment_config = SETTINGS.get("momentum_segment_thresholds") or {}

    if segment_config:
        breakpoints = SETTINGS.get("momentum_liquidity_breakpoints", {}) or {}
        high_cutoff = float(breakpoints.get("high", 1_000_000))
        low_cutoff = float(breakpoints.get("low", 300_000))
        try:
            avg_vol = safe_float(df["vol_avg10"].iloc[-1]) if df is not None else 0.0
        except (KeyError, ValueError, IndexError):
            avg_vol = 0.0

        if avg_vol >= high_cutoff:
            segment = "high_liquidity"
        elif avg_vol <= low_cutoff:
            segment = "low_liquidity"
        else:
            segment = "mid_liquidity"

        seg_value = segment_config.get(segment) if segment else None
        try:
            segment_threshold = float(seg_value) if seg_value is not None else None
        except (TypeError, ValueError):
            segment_threshold = None

    z_threshold = float(segment_threshold or base_threshold)

    # Dynamic threshold calibration
    dynamic_enabled = bool(SETTINGS.get("momentum_dynamic_enabled", False))
    dynamic_window = int(
        SETTINGS.get("momentum_dynamic_window", baseline_window) or baseline_window
    )
    dynamic_quantile = float(SETTINGS.get("momentum_dynamic_quantile", 0.975))
    dynamic_alpha = float(SETTINGS.get("momentum_dynamic_alpha", 0.5))
    dynamic_min = float(SETTINGS.get("momentum_dynamic_min", 1.0))
    dynamic_max = float(SETTINGS.get("momentum_dynamic_max", 3.0))

    metrics = []
    dynamic_candidates = []

    for horizon in horizons:
        if len(close) <= horizon:
            continue
        try:
            current_price = safe_float(close.iloc[-1])
            reference_price = safe_float(close.iloc[-(horizon + 1)])
            if reference_price == 0:
                continue

            return_fraction = (current_price - reference_price) / reference_price
            momentum_series = close.pct_change(horizon).dropna()
            recent_window = momentum_series.tail(baseline_window)

            if recent_window.empty:
                mean_fraction = 0.0
                std_fraction = 0.0
            else:
                mean_fraction = float(recent_window.mean())
                std_fraction = float(recent_window.std(ddof=0))

            if std_fraction > 1e-9:
                z_score = (return_fraction - mean_fraction) / std_fraction
            else:
                z_score = 0.0

            metrics.append(
                {
                    "horizon": horizon,
                    "return_pct": return_fraction * 100.0,
                    "mean_pct": mean_fraction * 100.0,
                    "std_pct": std_fraction * 100.0,
                    "zscore": z_score,
                }
            )

            if dynamic_enabled:
                window_len = max(dynamic_window, baseline_window)
                history = momentum_series.tail(window_len)
                if len(history) >= max(10, window_len // 3):
                    hist_mean = float(history.mean())
                    hist_std = float(history.std(ddof=0))
                    if hist_std > 1e-9:
                        z_hist = (history - hist_mean) / hist_std
                        z_hist = z_hist.dropna().abs()
                        if not z_hist.empty:
                            candidate = float(z_hist.quantile(dynamic_quantile))
                            if math.isfinite(candidate) and candidate > 0:
                                dynamic_candidates.append(candidate)
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            logger.debug("Momentum calculation for horizon %d failed: %s", horizon, e)
            continue

    dynamic_threshold = None
    if dynamic_candidates:
        dynamic_threshold = median(dynamic_candidates)
        dynamic_threshold = max(dynamic_min, min(dynamic_max, dynamic_threshold))
        z_threshold = (dynamic_alpha * dynamic_threshold) + ((1.0 - dynamic_alpha) * z_threshold)

    z_threshold = max(dynamic_min, min(dynamic_max, float(z_threshold)))

    best_metric = max(metrics, key=lambda item: abs(item["zscore"])) if metrics else None
    dominant_z = float(best_metric["zscore"]) if best_metric else 0.0
    dominant_return = float(best_metric["return_pct"]) if best_metric else 0.0
    direction = 1 if dominant_z >= z_threshold else (-1 if dominant_z <= -z_threshold else 0)

    positive = any(item["zscore"] >= z_threshold for item in metrics)
    negative = any(item["zscore"] <= -z_threshold for item in metrics)

    return {
        "metrics": metrics,
        "best": best_metric,
        "positive": positive,
        "negative": negative,
        "dominant_zscore": dominant_z,
        "dominant_return_pct": dominant_return,
        "dominant_direction": direction,
        "z_threshold_effective": z_threshold,
        "z_threshold_base": base_threshold,
        "z_threshold_segment": segment_threshold,
        "z_threshold_dynamic": dynamic_threshold,
        "liquidity_segment": segment,
        "baseline_window": baseline_window,
        "dynamic_threshold_samples": len(dynamic_candidates),
    }


def check_price_momentum(df: pd.DataFrame) -> bool:
    """
    Check for positive price momentum.

    Args:
        df: DataFrame with price data

    Returns:
        True if positive momentum detected
    """
    analysis = analyze_price_momentum(df)
    return bool(analysis.get("positive"))


# ---- Trend Analysis ----
def check_trend_strength(df: pd.DataFrame) -> bool:
    """
    Check trend strength: EMA50 vs EMA200 gap exceeds threshold.

    Args:
        df: DataFrame with 'ema50' and 'ema200' columns

    Returns:
        True if trend is strong (EMA50 > EMA200 by configured percentage)
    """
    if len(df) < 200:
        return False
    try:
        ema50 = safe_float(df["ema50"].iloc[-1])
        ema200 = safe_float(df["ema200"].iloc[-1])
        if ema200 == 0:
            return False
        strength_pct = ((ema50 - ema200) / ema200) * 100
        return strength_pct >= SETTINGS.get("trend_gap_pct", 3.0)
    except (KeyError, ValueError, ZeroDivisionError) as e:
        logger.debug("Trend strength check failed: %s", e)
        return False


# ---- Timeframe Alignment ----
def check_timeframe_alignment(
    df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_1d: pd.DataFrame
) -> Tuple[bool, float, List[bool]]:
    """
    Check trend alignment across 3 timeframes.
    At least 2/3 timeframes must be in the same direction.

    Args:
        df_1h: 1-hour timeframe DataFrame
        df_4h: 4-hour timeframe DataFrame
        df_1d: Daily timeframe DataFrame

    Returns:
        Tuple of (is_aligned, alignment_ratio, individual_alignments)
    """
    alignments = []

    try:
        # 1-hour trend (EMA20 vs Price)
        if len(df_1h) >= 20:
            price_1h = safe_float(df_1h["Close"].iloc[-1])
            ema20_1h = safe_float(df_1h["Close"].ewm(span=20).mean().iloc[-1])
            trend_1h = price_1h > ema20_1h
            alignments.append(trend_1h)

        # 4-hour trend (EMA50 vs Price)
        if len(df_4h) >= 50:
            price_4h = safe_float(df_4h["Close"].iloc[-1])
            ema50_4h = safe_float(df_4h["ema50"].iloc[-1])
            trend_4h = price_4h > ema50_4h
            alignments.append(trend_4h)

        # Daily trend (EMA200 vs Price)
        if len(df_1d) >= 200:
            price_1d = safe_float(df_1d["Close"].iloc[-1])
            ema200_1d = safe_float(df_1d["ema200"].iloc[-1])
            trend_1d = price_1d > ema200_1d
            alignments.append(trend_1d)

        # At least 2/3 alignment?
        if len(alignments) >= 2:
            bullish_count = sum(alignments)
            total_count = len(alignments)
            alignment_ratio = bullish_count / total_count

            # 67%+ alignment = strong signal
            return alignment_ratio >= 0.67, alignment_ratio, alignments

        return False, 0.0, alignments

    except (KeyError, ValueError, IndexError) as e:
        logger.debug("Timeframe alignment check failed: %s", e)
        return False, 0.0, []


def check_momentum_confluence(df_15m: pd.DataFrame, df_4h: pd.DataFrame) -> Tuple[bool, float]:
    """
    Check momentum indicator confluence across timeframes.
    Uses stricter criteria for quality improvement.

    Args:
        df_15m: 15-minute timeframe DataFrame
        df_4h: 4-hour timeframe DataFrame

    Returns:
        Tuple of (has_confluence, confluence_ratio)
    """
    try:
        confluence_score = 0
        max_score = 6  # 6 criteria total

        # 15m RSI momentum - tighter range
        if len(df_15m) >= 14:
            rsi_15m = safe_float(df_15m["rsi"].iloc[-1])
            if 45 <= rsi_15m <= 65:  # Narrower healthy range
                confluence_score += 1

        # 4h RSI momentum - tighter range
        if len(df_4h) >= 14:
            rsi_4h = safe_float(df_4h["rsi"].iloc[-1])
            if 45 <= rsi_4h <= 65:
                confluence_score += 1

        # 15m MACD histogram - strong positive
        if len(df_15m) >= 26:
            macd_15m = safe_float(df_15m["macd_hist"].iloc[-1])
            if macd_15m > 0.01:  # Not just positive, strongly positive
                confluence_score += 1

        # 4h MACD histogram - strong positive
        if len(df_4h) >= 26:
            macd_4h = safe_float(df_4h["macd_hist"].iloc[-1])
            if macd_4h > 0.01:
                confluence_score += 1

        # NEW: RSI trend check
        if len(df_15m) >= 15 and len(df_4h) >= 15:
            rsi_15m_prev = safe_float(df_15m["rsi"].iloc[-2])
            rsi_15m_curr = safe_float(df_15m["rsi"].iloc[-1])
            if rsi_15m_curr > rsi_15m_prev:  # RSI rising
                confluence_score += 1

        # NEW: MACD trend check
        if len(df_4h) >= 27:
            macd_4h_prev = safe_float(df_4h["macd_hist"].iloc[-2])
            macd_4h_curr = safe_float(df_4h["macd_hist"].iloc[-1])
            if macd_4h_curr > macd_4h_prev:  # MACD strengthening
                confluence_score += 1

        confluence_ratio = confluence_score / max_score
        return confluence_ratio >= 0.5, confluence_ratio  # 50%+ (3+ of 6 criteria)

    except (KeyError, ValueError, ZeroDivisionError) as e:
        logger.debug("Momentum confluence check failed: %s", e)
        return False, 0.0


# ---- Signal Scoring ----
def signal_score_row(df: pd.DataFrame) -> int:
    """
    Calculate signal score for the latest row.

    Checks:
    - Bollinger Band breakout
    - RSI recovery from oversold
    - MACD histogram crossover
    - Volume spike

    Args:
        df: DataFrame with indicator columns

    Returns:
        Signal score (0-4)
    """
    if len(df) < 2:
        return 0
    row = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0

    try:
        # Bollinger band signal
        if (
            not pd.isna(prev["Close"])
            and not pd.isna(prev["bb_lower"])
            and not pd.isna(row["Close"])
            and not pd.isna(row["bb_lower"])
        ):
            if safe_float(prev["Close"]) < safe_float(prev["bb_lower"]) and safe_float(
                row["Close"]
            ) > safe_float(row["bb_lower"]):
                score += 1

        # RSI signal
        if not pd.isna(row["rsi"]) and not pd.isna(prev["rsi"]):
            if 30 <= safe_float(row["rsi"]) <= 45 and safe_float(row["rsi"]) > safe_float(
                prev["rsi"]
            ):
                score += 1

        # MACD histogram signal
        if not pd.isna(prev["macd_hist"]) and not pd.isna(row["macd_hist"]):
            if safe_float(prev["macd_hist"]) < 0 and safe_float(row["macd_hist"]) > 0:
                score += 1

        # Volume signal
        if not pd.isna(row["Volume"]) and not pd.isna(row["vol_med20"]):
            if safe_float(row["Volume"]) >= safe_float(row["vol_med20"]) * 1.2:
                score += 1
    except (KeyError, ValueError, TypeError) as e:
        logger.debug("Signal score calculation failed: %s", e)
        return 0

    return score


# ---- Recommendation Scoring ----
MAX_RECO_SCORE = 18.3  # Theoretical maximum with premium bonus


def compute_recommendation_score(row: Dict[str, Any]) -> float:
    """
    Compute composite recommendation score from signal components.

    Args:
        row: Dictionary with signal data

    Returns:
        Recommendation score (0 to ~18.3)
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
    score += 0.3 if bool(row.get("is_premium_symbol", False)) else 0.0
    return round(score, 3)


def compute_recommendation_strength(x: Any) -> int:
    """
    Scale recommendation score to 0-100 range.

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


# ---- Explanation Builders ----
def build_explanation(row: Dict[str, Any]) -> str:
    """
    Build human-readable explanation for a signal.

    Args:
        row: Signal data dictionary

    Returns:
        Explanation string
    """
    try:
        regime = bool(row.get("regime"))
        direction = bool(row.get("direction"))
        trend = "Up" if (regime and direction) else ("Mixed" if (regime or direction) else "Down")
        ar = int(float(row.get("alignment_ratio", 0)) * 100)
        mr = int(float(row.get("momentum_ratio", 0)) * 100)
        fs = int(row.get("filter_score", 0))
        return f"Trend {trend} | Uyum Z{ar}%/M{mr}% | Filtre {fs}/3"
    except (KeyError, ValueError, TypeError):
        return "Özet yok"


def build_reason(row: Dict[str, Any]) -> str:
    """
    Build actionable reason for a signal decision.

    Args:
        row: Signal data dictionary

    Returns:
        Reason string with action guidance
    """
    try:
        rr = row.get("risk_reward") or 0
        sl = row.get("stop_loss")
        tp = row.get("take_profit")

        if row.get("entry_ok"):
            return f"Alınır: Trend+ Uyum+ | R/R {rr:.1f} | SL ${sl} · TP ${tp}"

        # List missing criteria
        lacks = []
        if not row.get("volume_spike"):
            lacks.append("Hacim")
        if not row.get("price_momentum"):
            lacks.append("Momentum")
        if not row.get("trend_strength"):
            lacks.append("Trend")
        if not row.get("timeframe_aligned"):
            lacks.append("Uyum")
        if not row.get("momentum_confluence"):
            lacks.append("Mom.Uyum")

        lacks_str = ",".join(lacks[:2]) if lacks else "Onay bekleyin"
        return f"Bekleyin: Eksik {lacks_str} | R/R {rr:.1f}"
    except (KeyError, ValueError, TypeError):
        return "Neden yok"
